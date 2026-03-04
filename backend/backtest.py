"""
バックテスト & 精度評価スクリプト
====================================
2015〜2024年のデータで「2025年出題」を予測し、実際の出題と照合する。

実行方法:
  python3 backtest.py

出力:
  - コンソールに精度レポート
  - backtest_result.json に詳細結果
"""
import sys
import json
import numpy as np
from collections import defaultdict
from sqlalchemy import func
from sqlalchemy.orm import Session

sys.path.insert(0, '.')
from database import SessionLocal
from models import Question, QuestionTopic, Topic, Law, Subject

# ------- バックテスト設定 -------
TRAIN_MIN_YEAR = 2015
TRAIN_MAX_YEAR = 2024   # この年度まででモデルを学習
TEST_YEAR      = 2025   # この年度を予測対象とする
N_TRAIN_YEARS  = TRAIN_MAX_YEAR - TRAIN_MIN_YEAR + 1
GAMMA_FORGET   = 0.85


def build_timeseries_upto(db: Session, max_year: int):
    """指定年度まで（含む）の時系列データを構築。"""
    results = (
        db.query(
            QuestionTopic.topic_id,
            Question.year,
            func.count(Question.id).label("cnt"),
        )
        .join(Question, QuestionTopic.question_id == Question.id)
        .filter(Question.year >= TRAIN_MIN_YEAR, Question.year <= max_year)
        .group_by(QuestionTopic.topic_id, Question.year)
        .all()
    )
    n = max_year - TRAIN_MIN_YEAR + 1
    ts = defaultdict(lambda: [0] * n)
    for r in results:
        idx = r.year - TRAIN_MIN_YEAR
        ts[r.topic_id][idx] += r.cnt
    return dict(ts)


def get_actual_topics_in_year(db: Session, year: int):
    """指定年度に実際に出題されたトピックIDの集合を返す。"""
    rows = (
        db.query(QuestionTopic.topic_id)
        .join(Question, Question.id == QuestionTopic.question_id)
        .filter(Question.year == year)
        .distinct()
        .all()
    )
    return set(r.topic_id for r in rows)


def linear_regression_score(series):
    x = np.arange(len(series), dtype=float)
    y = np.array(series, dtype=float)
    if len(x) < 2 or y.sum() == 0:
        return 0.0
    x_mean, y_mean = x.mean(), y.mean()
    ss_xy = np.sum((x - x_mean) * (y - y_mean))
    ss_xx = np.sum((x - x_mean) ** 2)
    if ss_xx == 0:
        return y_mean
    slope = ss_xy / ss_xx
    return max(slope * len(series) + (y_mean - slope * x_mean), 0.0)


def recency_score(series, decay=0.3):
    n = len(series)
    total, wsum = 0.0, 0.0
    for i, c in enumerate(series):
        w = np.exp(-decay * (n - 1 - i))
        total += c * w
        wsum  += w
    return total / wsum if wsum else 0.0


def gap_urgency(series, target_offset):
    """最終出題からの間隔スコア。target_offsetは学習年数。"""
    appearances = [i for i, v in enumerate(series) if v > 0]
    if not appearances:
        return 0.0
    last = appearances[-1]
    gap = target_offset - last  # 次の年（テスト年）と最終出題の差
    last_count = series[last]
    if gap <= 1:
        base = 0.4 + min(last_count / 10.0, 0.2)
    elif gap == 2:
        base = 0.75
    elif gap == 3:
        base = 1.0
    elif gap == 4:
        base = 0.9
    elif gap == 5:
        base = 0.7
    else:
        base = max(0.5 - (gap - 6) * 0.1, 0.05)
    avg_when = np.mean([series[i] for i in appearances])
    return min(base + min(avg_when / 5.0, 0.2), 1.0)


def cycle_score(series):
    appearances = [i for i, v in enumerate(series) if v > 0]
    n = len(appearances)
    if n < 2:
        return 0.0
    n_years = len(series)
    if n >= n_years - 1:
        counts = np.array(series, dtype=float)
        mean_c = counts.mean()
        if mean_c == 0:
            return 0.5
        cv = counts.std() / mean_c
        recent_avg = counts[-3:].mean()
        overall_avg = counts.mean()
        ratio = min(recent_avg / max(overall_avg, 0.01), 2.0) / 2.0
        return min(0.3 + 0.4 * ratio + 0.3 * (1.0 - min(cv, 1.0)), 1.0)
    gaps = [appearances[i+1] - appearances[i] for i in range(n-1)]
    avg_gap = np.mean(gaps)
    std_gap = np.std(gaps) if len(gaps) > 1 else avg_gap * 0.5
    last = appearances[-1]
    years_since = n_years - last  # to the target (one past last train year)
    if avg_gap == 0:
        return 0.5
    alignment = 1.0 - min(abs(years_since - avg_gap) / max(avg_gap, 1), 1.0)
    consistency = 1.0 / (1.0 + std_gap)
    return alignment * consistency


def bayesian_score(series):
    alpha, beta = 1.0, 1.0
    dec_s, dec_t = 0.0, 0.0
    n = len(series)
    for i, v in enumerate(series):
        w = GAMMA_FORGET ** (n - 1 - i)
        if v > 0:
            dec_s += w
        dec_t += w
    return (alpha + dec_s) / (alpha + beta + dec_t)


def compute_score(series):
    n = len(series)
    data_years = sum(1 for v in series if v > 0)
    if data_years == 0:
        return 0.0
    confidence = 0.6 if data_years <= 2 else 1.0

    trend   = min(linear_regression_score(series) / 6.0, 1.0)
    recency = min(recency_score(series) / 6.0, 1.0)
    cycle   = cycle_score(series)
    gap     = gap_urgency(series, n)   # target is one step beyond training
    bayes   = bayesian_score(series)

    score = 0.30 * trend + 0.20 * cycle + 0.25 * recency + 0.15 * gap + 0.10 * bayes
    return score * confidence


def precision_at_k(predicted_ids, actual_ids, k):
    top_k = predicted_ids[:k]
    hits  = sum(1 for t in top_k if t in actual_ids)
    return hits / k


def recall_at_k(predicted_ids, actual_ids, k):
    if not actual_ids:
        return 0.0
    top_k = set(predicted_ids[:k])
    hits  = len(top_k & actual_ids)
    return hits / len(actual_ids)


def run_backtest():
    db = SessionLocal()
    try:
        # ── 学習データ構築（〜2024年）
        timeseries = build_timeseries_upto(db, TRAIN_MAX_YEAR)

        # ── 全トピック取得
        topics = (
            db.query(Topic, Law, Subject)
            .join(Law, Topic.law_id == Law.id)
            .join(Subject, Law.subject_id == Subject.id)
            .all()
        )

        # ── 各トピックのスコアを計算
        scored = []
        for topic, law, subject in topics:
            series  = timeseries.get(topic.id, [0] * N_TRAIN_YEARS)
            score   = compute_score(series)
            data_yrs = sum(1 for v in series if v > 0)
            scored.append({
                "topic_id":     topic.id,
                "topic_name":   topic.name,
                "law_name":     law.name,
                "subject_name": subject.name,
                "score":        round(score * 100, 2),
                "data_years":   data_yrs,
                "total_q":      sum(series),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        predicted_ids = [s["topic_id"] for s in scored]

        # ── 2025年の実際の出題トピック
        actual_ids = get_actual_topics_in_year(db, TEST_YEAR)

        # ── 評価指標
        p10  = precision_at_k(predicted_ids, actual_ids, 10)
        p20  = precision_at_k(predicted_ids, actual_ids, 20)
        p30  = precision_at_k(predicted_ids, actual_ids, 30)
        r10  = recall_at_k(predicted_ids, actual_ids, 10)
        r20  = recall_at_k(predicted_ids, actual_ids, 20)
        r30  = recall_at_k(predicted_ids, actual_ids, 30)

        # ── ランダム基準（baseline）
        total_topics = len(scored)
        actual_count = len(actual_ids)
        random_p = actual_count / total_topics  # ランダムに選んだ場合の期待precision

        print("=" * 60)
        print("2025年度 出題予測バックテスト結果")
        print("=" * 60)
        print(f"  学習データ：{TRAIN_MIN_YEAR}〜{TRAIN_MAX_YEAR}年")
        print(f"  テスト年度：{TEST_YEAR}年")
        print(f"  全トピック数：{total_topics}")
        print(f"  2025年 実際の出題トピック数：{actual_count}")
        print(f"  ランダム予測の期待Precision：{random_p*100:.1f}%")
        print()
        print("  Precision（上位N件の命中率）:")
        print(f"    P@10:  {p10*100:.1f}%  （ランダム比: ×{p10/random_p:.1f}）")
        print(f"    P@20:  {p20*100:.1f}%  （ランダム比: ×{p20/random_p:.1f}）")
        print(f"    P@30:  {p30*100:.1f}%  （ランダム比: ×{p30/random_p:.1f}）")
        print()
        print("  Recall（全実出題トピックのうち何%をキャプチャ）:")
        print(f"    R@10:  {r10*100:.1f}%")
        print(f"    R@20:  {r20*100:.1f}%")
        print(f"    R@30:  {r30*100:.1f}%")
        print()

        # ── 上位30の詳細と実際の出題との照合
        print("  上位30トピック（◎=2025年実出題、✗=不出題）:")
        print(f"  {'Rank':<5} {'Hit':<4} {'Score':>6} {'Topic':<30} {'Law'}")
        print("  " + "-" * 70)
        for rank, s in enumerate(scored[:30], 1):
            hit = "◎" if s["topic_id"] in actual_ids else "✗"
            print(f"  {rank:<5} {hit:<4} {s['score']:>6.1f}  {s['topic_name']:<30} {s['law_name']}")

        print()
        print("  実出題だが上位30に入らなかったトピック（見逃し）:")
        top30_ids = set(predicted_ids[:30])
        missed = [t for t in scored if t["topic_id"] in actual_ids and t["topic_id"] not in top30_ids]
        for s in missed:
            rank = predicted_ids.index(s["topic_id"]) + 1
            print(f"    Rank{rank:>3}: {s['topic_name']}（{s['law_name']}）score={s['score']}")

        # ── JSON保存
        result = {
            "train_range": f"{TRAIN_MIN_YEAR}-{TRAIN_MAX_YEAR}",
            "test_year":   TEST_YEAR,
            "total_topics": total_topics,
            "actual_topic_count": actual_count,
            "random_baseline_precision": round(random_p * 100, 1),
            "metrics": {
                "precision_at_10": round(p10 * 100, 1),
                "precision_at_20": round(p20 * 100, 1),
                "precision_at_30": round(p30 * 100, 1),
                "recall_at_10":    round(r10 * 100, 1),
                "recall_at_20":    round(r20 * 100, 1),
                "recall_at_30":    round(r30 * 100, 1),
            },
            "predictions": scored,
            "actual_2025_topic_ids": sorted(actual_ids),
        }
        with open("backtest_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("  詳細結果を backtest_result.json に保存しました。")

    finally:
        db.close()


if __name__ == "__main__":
    run_backtest()
