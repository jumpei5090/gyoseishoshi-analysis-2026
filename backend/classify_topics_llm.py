"""
LLM によるトピック自動再分類スクリプト
=========================================
Gemini API を使って全629問を100トピックに自動分類し、
現在のDB分類と比較して差異のある問題を検出・修正する。

使い方:
  export GOOGLE_API_KEY="your-key-here"

  # ドライラン（最初の10問のみ）
  python3 classify_topics_llm.py --dry-run

  # 特定科目のみ
  python3 classify_topics_llm.py --subject 行政法

  # 全問分類
  python3 classify_topics_llm.py

  # DBに適用（確信度85%以上のみ）
  python3 classify_topics_llm.py --save --confidence 85
"""
import sys
import os
import json
import time
import csv
from typing import Optional

sys.path.insert(0, '.')
from database import SessionLocal
from models import Question, QuestionTopic, Topic, Law, Subject

# ────────────────────────────────────────
# 設定
# ────────────────────────────────────────
CONFIDENCE_AUTO   = 85   # これ以上は自動適用候補
CONFIDENCE_REVIEW = 70   # これ以上は要確認リスト
MODEL_NAME        = "gemini-2.5-flash"
RPM_LIMIT         = 50    # 有料枠設定済みのため、高速に処理
RESULT_PATH       = os.path.join(os.path.dirname(__file__), "classification_result.json")
CANDIDATES_PATH   = os.path.join(os.path.dirname(__file__), "reclassify_candidates.csv")


def get_api_key() -> Optional[str]:
    """APIキーを環境変数または .env から取得。複数エンコーディングに対応。"""
    # 優先①: 環境変数
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if key and key.strip():
        return key.strip()

    # 優先②: .env ファイル（複数箇所・複数エンコーディングを試す）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(script_dir, ".env"),
        os.path.join(os.getcwd(), ".env"),
        os.path.join(os.path.dirname(script_dir), ".env"),
    ]
    for env_file in candidates:
        if not os.path.exists(env_file):
            continue
        for encoding in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                with open(env_file, encoding=encoding) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("GOOGLE_API_KEY="):
                            val = line.split("=", 1)[1].strip().strip('"').strip("'")
                            if val:
                                return val
            except Exception:
                continue
    return None


def build_topic_label(topic: Topic, law: Law, subject: Subject) -> str:
    return f"[{subject.name}] {law.name} > {topic.name}（ID:{topic.id}）"


def make_prompt(question_text: str, topic_labels: list[str]) -> str:
    labels_str = "\n".join(f"  {i+1}. {lbl}" for i, lbl in enumerate(topic_labels))
    return f"""あなたは日本最高峰の行政書士試験対策の専門家であり、法学科教授です。
以下の「行政書士試験 過去問」を分析し、与えられた100個のトピックの中から【最も適切かつ具体的な】ものを1つだけ選択してください。

### 分類の極意（Few-Shot Examples）:
1. 憲法: 「司法権の限界（統治行為論、部分社会の法理等）についての判例...」
   → 正解: [憲法] 裁判所（「国会」や「内閣」ではありません）
2. 行政法: 「行政上の義務履行確保（代執行、直接強制、執行罰、強制徴収）...」
   → 正解: [行政法] 行政上の強制執行（具体的な手段が並んでいる場合はこの総括的項目が適切）
3. 行政法: 「地方自治法に基づく議会の解散、議員の除名、住民投票...」
   → 正解: [行政法] 住民・議会（「地方自治法」全体の項目より具体的です）
4. 民法: 「AがBに対して建物を売却したが、登記未了の間にCに二重譲渡され...」
   → 正解: [民法] 物権変動（「契約総論」や「不法行為」ではなく物権の問題です）
5. 憲法: 「検閲の禁止や、出版物の差止め、通信の秘密...」
   → 正解: [憲法] 表現の自由（精神的自由の代表的な項目です）

### 回答時の思考プロセス:
1. 問題がどの科目（憲法、行政法、民法等）に属するか特定する。
2. 条拠（条文知識）か判拠（判例知識）かを確認する。
3. トピック一覧から、専門家として最も「座りの良い」具体的な項目を1つ選ぶ。

## 問題文
{question_text[:1000]}

## 選択肢（トピック一覧）
{labels_str}

## 回答形式（JSONのみ。余計な説明は一切不要）
{{
  "topic_number": <上記リストの1〜{len(topic_labels)}の番号>,
  "confidence": <確信度（0〜100）>,
  "selection_process": "<選んだ論理的根拠を15文字以内で簡潔に>",
  "reason": "<さらに詳細な理由を30文字以内で>"
}}"""


def classify_question(model, question_text: str, topic_labels: list, retries: int = 3) -> Optional[dict]:
    """1問を分類して結果を返す。失敗時はNone。"""
    prompt = make_prompt(question_text, topic_labels)
    import re
    for attempt in range(retries):
        try:
            resp = model.generate_content(prompt)
            text = resp.text.strip()
            # ```json ... ``` を除去
            text = re.sub(r"```json\s*", "", text)
            text = re.sub(r"```\s*$", "", text).strip()
            # テキスト内に JSON オブジェクトを抽出（前後に文章がある場合も対応）
            m = re.search(r'\{[^{}]+\}', text, re.DOTALL)
            if m:
                return json.loads(m.group(0))
            return json.loads(text)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "ResourceExhausted" in err_str:
                wait = 65 * (attempt + 1)
                print(f"\n  ⚠️  レート制限 → {wait}秒待機 (試行{attempt+1}/{retries})", flush=True)
                time.sleep(wait)
            elif attempt == retries - 1:
                print(f"\n  ✗ 解析失敗: {err_str[:120]}")
    return None


def run(
    dry_run: bool = False,
    subject_filter: Optional[str] = None,
    save_to_db: bool = False,
    confidence_threshold: int = CONFIDENCE_AUTO,
):
    # ── APIキー取得
    api_key = get_api_key()
    if not api_key:
        print("❌ GOOGLE_API_KEY が設定されていません。")
        print("   backend/.env に GOOGLE_API_KEY=your-key を追加してください。")
        sys.exit(1)

    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.0,
        }
    )
    print(f"✓ Gemini API ({MODEL_NAME}) 接続確認")

    db = SessionLocal()
    try:
        # ── 全トピック取得
        topics_raw = (
            db.query(Topic, Law, Subject)
            .join(Law, Topic.law_id == Law.id)
            .join(Subject, Law.subject_id == Subject.id)
            .order_by(Subject.id, Law.id, Topic.id)
            .all()
        )
        topic_labels = [build_topic_label(t, l, s) for t, l, s in topics_raw]
        topic_ids    = [t.id for t, l, s in topics_raw]
        topic_map    = {t.id: (t, l, s) for t, l, s in topics_raw}

        # ── 既存の結果をロードしてレジューム対応
        results = []
        already_processed_ids = set()
        if os.path.exists(RESULT_PATH):
            try:
                with open(RESULT_PATH, "r", encoding="utf-8") as f:
                    results = json.load(f)
                    already_processed_ids = {r["question_id"] for r in results if r.get("status") not in ("parse_error", "invalid_number")}
                print(f"✓ 既存の結果から {len(already_processed_ids)} 問をロードしました（再開モード）")
            except Exception:
                pass

        # ── 対象問題取得
        query = db.query(Question)
        if subject_filter:
            query = query.join(Subject, Question.subject_id == Subject.id)\
                         .filter(Subject.name == subject_filter)
        questions = query.order_by(Question.year, Question.question_number).all()
        
        # 処理対象を絞り込む（すでに完了しているものはスキップ）
        if not dry_run:
            questions = [q for q in questions if q.id not in already_processed_ids]
        else:
            questions = questions[:10]

        print(f"処理対象: {len(questions)}問  トピック数: {len(topic_labels)}")
        if dry_run:
            print("（ドライランモード: 最初の10問のみ）")
        print()

        reclassify = []
        interval = 60 / RPM_LIMIT  # 秒

        for idx, q in enumerate(questions, 1):
            # 現在のトピック取得
            current_assignments = (
                db.query(QuestionTopic, Topic, Law, Subject)
                .join(Topic, QuestionTopic.topic_id == Topic.id)
                .join(Law, Topic.law_id == Law.id)
                .join(Subject, Law.subject_id == Subject.id)
                .filter(QuestionTopic.question_id == q.id)
                .all()
            )
            current_topic_ids = [qt.topic_id for qt, t, l, s in current_assignments]
            current_topic_names = [t.name for qt, t, l, s in current_assignments]

            print(f"[{idx:>3}/{len(questions)}] {q.year}年 問{q.question_number:>3} "
                  f"現在={'/'.join(current_topic_names)}", end=" ... ", flush=True)

            # Gemini で分類
            result = classify_question(model, q.question_text or "", topic_labels)

            if result is None:
                print("✗ 解析失敗")
                results.append({
                    "question_id": q.id, "year": q.year,
                    "question_number": q.question_number,
                    "status": "parse_error",
                })
                time.sleep(interval)
                continue

            topic_number = result.get("topic_number", 0)
            confidence   = result.get("confidence", 0)
            selection_process = result.get("selection_process", "")
            reason       = result.get("reason", "")

            if not (1 <= topic_number <= len(topic_labels)):
                print(f"✗ 無効番号={topic_number}")
                results.append({"question_id": q.id, "status": "invalid_number"})
                time.sleep(interval)
                continue

            suggested_topic_id   = topic_ids[topic_number - 1]
            suggested_topic_info = topic_map[suggested_topic_id]
            suggested_name       = suggested_topic_info[0].name

            is_different = suggested_topic_id not in current_topic_ids
            status = "same"
            if is_different:
                if confidence >= confidence_threshold:
                    status = "auto_reclassify"
                elif confidence >= CONFIDENCE_REVIEW:
                    status = "review"
                else:
                    status = "low_confidence"

            print(f"→ {suggested_name} (確信度:{confidence}%) [{status}]")
            if selection_process:
                print(f"     思考: {selection_process}")

            row = {
                "question_id":        q.id,
                "year":               q.year,
                "question_number":    q.question_number,
                "question_text":      (q.question_text or "")[:80],
                "current_topic_ids":  current_topic_ids,
                "current_topics":     current_topic_names,
                "suggested_topic_id": suggested_topic_id,
                "suggested_topic":    suggested_name,
                "confidence":         confidence,
                "selection_process":  selection_process,
                "reason":             reason,
                "status":             status,
            }
            results.append(row)

            if is_different and confidence >= CONFIDENCE_REVIEW:
                reclassify.append(row)

            # DB適用
            if save_to_db and status == "auto_reclassify":
                # 既存のトピック割り当てを確認
                existing = db.query(QuestionTopic)\
                    .filter(QuestionTopic.question_id == q.id)\
                    .all()
                if len(existing) == 1:
                    # 1対1の場合は差し替え
                    existing[0].topic_id = suggested_topic_id
                    db.commit()
                    print(f"  ✓ DB更新: {current_topic_names[0]} → {suggested_name}")

            # 5問毎に保存
            if idx % 5 == 0:
                with open(RESULT_PATH, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)

            time.sleep(interval)

        # ── サマリー
        total = len(results)
        auto  = sum(1 for r in results if r.get("status") == "auto_reclassify")
        rev   = sum(1 for r in results if r.get("status") == "review")
        same  = sum(1 for r in results if r.get("status") == "same")
        err   = sum(1 for r in results if r.get("status") in ("parse_error", "invalid_number", "low_confidence"))

        print()
        print("=" * 55)
        print(f"完了: {total}問")
        print(f"  同一トピック:      {same}問")
        print(f"  自動修正候補({confidence_threshold}%+): {auto}問")
        print(f"  要確認({CONFIDENCE_REVIEW}〜{confidence_threshold-1}%):     {rev}問")
        print(f"  スキップ/エラー:  {err}問")
        print("=" * 55)

        # ── JSON保存
        with open(RESULT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"詳細: {RESULT_PATH}")

        # ── 変更候補CSV
        if reclassify:
            with open(CANDIDATES_PATH, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "question_id", "year", "question_number", "question_text",
                    "current_topics", "suggested_topic", "confidence", "reason", "status"
                ])
                writer.writeheader()
                for r in reclassify:
                    writer.writerow({k: v for k, v in r.items() if k in writer.fieldnames})
            print(f"変更候補CSV: {CANDIDATES_PATH}")

    finally:
        db.close()


if __name__ == "__main__":
    args = sys.argv[1:]
    dry_run    = "--dry-run" in args
    save       = "--save" in args
    subj_idx   = args.index("--subject") + 1 if "--subject" in args else None
    subj       = args[subj_idx] if subj_idx and subj_idx < len(args) else None
    conf_idx   = args.index("--confidence") + 1 if "--confidence" in args else None
    conf       = int(args[conf_idx]) if conf_idx and conf_idx < len(args) else CONFIDENCE_AUTO

    run(dry_run=dry_run, subject_filter=subj, save_to_db=save, confidence_threshold=conf)
