"""
問題番号ルール検証スクリプト
==============================
行政書士試験の問題番号と科目の対応ルールをコードで定義し、
DBの登録内容と照合して乖離を検出・修正する。

実行方法:
  python3 validate_question_numbers.py           # 確認のみ
  python3 validate_question_numbers.py --fix     # 不一致を自動修正

問題構成（各年度で固定 or ほぼ固定）:
  問1〜2   : 基礎法学
  問3〜7   : 憲法
  問8〜26  : 行政法（択一）
  問27〜35 : 民法（択一）  ※年度により ±1
  問36〜40 : 商法・会社法  ※年度により問番 微差
  問41〜43 : 多肢選択（憲法 or 行政法 or 両方を含む行政法グループ）
  問44〜46 : 民法（記述）
  問47〜   : 一般知識（〜57 or 2025以降は〜60）
"""
import sys
sys.path.insert(0, '.')
from typing import Optional
from database import SessionLocal
from models import Question, Subject
from sqlalchemy import func

# ──────────────────────────────────────────
# 問題番号→期待科目 のルール定義
# 年度ごとの微差を吸収するため「厳格ルール」と「許容ルール」を設定
# ──────────────────────────────────────────

def get_expected_subject(question_number: int, year: int) -> Optional[str]:
    """
    問題番号・年度から期待される科目名を返す。
    Noneの場合はルール外（柔軟な境界域）= チェック対象外。
    """
    qn = question_number

    # 固定: 基礎法学
    if qn <= 2:
        return "基礎法学"

    # 固定: 憲法（択一）
    if 3 <= qn <= 7:
        return "憲法"

    # 行政法（択一本体）- 問8〜26
    if 8 <= qn <= 26:
        return "行政法"

    # 境界域: 問27〜35 は民法または行政法終端 → 民法が期待値
    if 27 <= qn <= 35:
        return "民法"

    # 境界域: 問36〜40
    # 2024年の問36だけは民法（相続）が出題されたため民法として例外扱い
    if qn == 36:
        if year == 2024:
            return "民法"
        else:
            return "商法・会社法"

    if 37 <= qn <= 40:
        return "商法・会社法"

    # 多肢選択域: 問41〜43 は行政法系（憲法・行政法の多肢選択）
    # 年によって問41=憲法、問42〜43=行政法 or 問41〜43=行政法
    # → ここは「憲法 or 行政法」の2択で許容
    if 41 <= qn <= 43:
        return None  # 柔軟（憲法・行政法の両方を許容）

    # 記述: 問44〜46 は民法（例外的に行政法のこともあるが通常民法）
    if 44 <= qn <= 46:
        return None  # 記述は年度で変化、チェック省略

    # 一般知識: 問47以降
    if qn >= 47:
        return "一般知識"

    return None


def run_validation(auto_fix: bool = False):
    db = SessionLocal()
    try:
        # 全科目のIDとname取得
        subjects = {s.name: s.id for s in db.query(Subject).all()}
        subject_by_id = {s.id: s.name for s in db.query(Subject).all()}

        print("=" * 65)
        print("問題番号ルール検証レポート")
        print("=" * 65)

        years = [r[0] for r in db.query(Question.year).distinct().order_by(Question.year).all()]
        total_checked = 0
        total_mismatch = 0
        all_mismatches = []

        for year in years:
            questions = db.query(Question).filter(Question.year == year)\
                .order_by(Question.question_number).all()

            year_mismatch = []
            for q in questions:
                expected_subj = get_expected_subject(q.question_number, year)
                if expected_subj is None:
                    continue  # チェック対象外

                actual_subj = subject_by_id.get(q.subject_id, "不明")
                total_checked += 1

                if actual_subj != expected_subj:
                    total_mismatch += 1
                    year_mismatch.append({
                        "year": year,
                        "question_id": q.id,
                        "question_number": q.question_number,
                        "actual_subject": actual_subj,
                        "expected_subject": expected_subj,
                        "format": q.question_format,
                    })
                    all_mismatches.append(year_mismatch[-1])

            if year_mismatch:
                print(f"\n  【{year}年】 {len(year_mismatch)}件の不一致:")
                for m in year_mismatch:
                    print(f"    問{m['question_number']:>3} ({m['format'] or '不明':<6})"
                          f" DB={m['actual_subject']:>10} → 期待={m['expected_subject']}")
            else:
                print(f"  【{year}年】 ✓ 全問題の科目分類に問題なし")

        print()
        print(f"  チェック総数: {total_checked}問")
        print(f"  不一致件数:   {total_mismatch}問")
        print(f"  一致率:       {((total_checked - total_mismatch) / max(total_checked, 1)) * 100:.1f}%")

        # ── 自動修正
        if auto_fix and all_mismatches:
            print()
            print("  ── 自動修正を実行します ──")
            fixed = 0
            for m in all_mismatches:
                new_subject_id = subjects.get(m["expected_subject"])
                if new_subject_id is None:
                    print(f"    ✗ 科目ID不明: {m['expected_subject']}")
                    continue

                q = db.query(Question).filter(Question.id == m["question_id"]).first()
                if q:
                    q.subject_id = new_subject_id
                    fixed += 1
                    print(f"    ✓ {m['year']}年 問{m['question_number']}: "
                          f"{m['actual_subject']} → {m['expected_subject']}")

            db.commit()
            print(f"\n  修正完了: {fixed}/{len(all_mismatches)}件")
        elif all_mismatches and not auto_fix:
            print()
            print("  ※ 修正するには --fix オプションをつけて再実行してください:")
            print("     python3 validate_question_numbers.py --fix")

        return all_mismatches

    finally:
        db.close()


if __name__ == "__main__":
    auto_fix = "--fix" in sys.argv
    run_validation(auto_fix=auto_fix)
