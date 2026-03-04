"""
2025年選択肢 インポートユーティリティ
=====================================================
目的:
  ① CSVテンプレートを生成（手入力用）
  ② 記入済みCSVをDBにインポート

現状:
  2025年（令和7年）の問題選択肢は、gyosyo.info が未公開（404）、
  goukakudojyo は会員制のため、スクレイピングによる自動取得が不可能。
  代わりに、手入力用CSVを生成/インポートするツールを提供する。

使い方:
  # Step1: テンプレートCSVを生成
  python3 scrape_choices_2025.py --export

  # Step2: 生成した choices_2025_template.csv を編集して選択肢テキストを入力

  # Step3: インポート（DB dry-run）
  python3 scrape_choices_2025.py --import

  # Step4: DBに保存
  python3 scrape_choices_2025.py --import --save

CSVフォーマット:
  question_id, year, question_number, choice_number, choice_text, is_correct
"""
import sys
import csv
import os
sys.path.insert(0, '.')
from database import SessionLocal
from models import Question, Choice
from sqlalchemy import exists

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "choices_2025_template.csv")
TARGET_YEAR   = 2025


def export_template():
    """2025年の欠損選択肢トピックのCSVテンプレートを生成する。"""
    db = SessionLocal()
    try:
        targets = (
            db.query(Question)
            .filter(
                Question.year == TARGET_YEAR,
                Question.question_format.in_(["5肢択一", "多肢選択"]),
                ~exists().where(Choice.question_id == Question.id),
            )
            .order_by(Question.question_number)
            .all()
        )
        print(f"対象問題: {len(targets)}問（2025年 選択肢なし）")
        if not targets:
            print("すでに全問選択肢が登録されています。")
            return

        rows = []
        for q in targets:
            n_choices = 5 if q.question_format == "5肢択一" else 4
            correct = str(q.correct_answer or "").strip()
            for i in range(1, n_choices + 1):
                try:
                    is_correct = (int(correct) == i)
                except ValueError:
                    is_correct = False
                rows.append({
                    "question_id":     q.id,
                    "year":            q.year,
                    "question_number": q.question_number,
                    "format":          q.question_format,
                    "correct_answer":  correct,
                    "choice_number":   i,
                    "choice_text":     "",   # ← ここを記入
                    "is_correct":      "TRUE" if is_correct else "FALSE",
                })

        with open(TEMPLATE_PATH, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)

        print(f"テンプレート出力完了: {TEMPLATE_PATH}")
        print(f"生成行数: {len(rows)}行（{len(targets)}問 × 4〜5択）")
        print()
        print("次のステップ:")
        print("  1. 上記CSVを開き、choice_text 列に選択肢テキストを入力")
        print("  2. python3 scrape_choices_2025.py --import  でインポートを確認")
        print("  3. python3 scrape_choices_2025.py --import --save  でDB書き込み")

    finally:
        db.close()


def import_from_csv(save: bool = False):
    """記入済みCSVをDBにインポートする。"""
    if not os.path.exists(TEMPLATE_PATH):
        print(f"CSVファイルが見つかりません: {TEMPLATE_PATH}")
        print("まず --export でテンプレートを生成してください。")
        return

    db = SessionLocal()
    try:
        with open(TEMPLATE_PATH, "r", encoding="utf-8-sig") as f:
            rows = list(csv.DictReader(f))

        # choice_text が空の行をチェック
        empty = [r for r in rows if not r.get("choice_text", "").strip()]
        if empty:
            print(f"⚠️  {len(empty)}行の choice_text が未入力です。")
            for r in empty[:5]:
                print(f"   問{r['question_number']} 選択肢{r['choice_number']}")
            if len(empty) > 5:
                print(f"   ...（他 {len(empty)-5}行）")

        filled = [r for r in rows if r.get("choice_text", "").strip()]
        print(f"インポート対象: {len(filled)}行（空行スキップ: {len(empty)}行）")

        if not filled:
            print("インポートできる行がありません。CSVのchoice_text列を入力してください。")
            return

        if save:
            inserted = 0
            skipped  = 0
            for r in filled:
                q_id  = int(r["question_id"])
                c_num = int(r["choice_number"])
                # 既存チェック
                existing = db.query(Choice)\
                    .filter(Choice.question_id == q_id, Choice.choice_number == c_num)\
                    .first()
                if existing:
                    skipped += 1
                    continue
                choice = Choice(
                    question_id   = q_id,
                    choice_number = c_num,
                    choice_text   = r["choice_text"].strip(),
                    is_correct    = r.get("is_correct", "FALSE").upper() == "TRUE",
                )
                db.add(choice)
                inserted += 1
            db.commit()
            print(f"✓ DB書き込み完了: {inserted}件挿入 / {skipped}件スキップ（既存）")
        else:
            print("--- ドライラン（最初の5件を表示）---")
            for r in filled[:5]:
                print(f"  問{r['question_number']} 選択肢{r['choice_number']}: {r['choice_text'][:60]}")
            print("※ DBに書き込む場合は --save を追加してください。")

    finally:
        db.close()


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--export" in args:
        export_template()
    elif "--import" in args:
        save = "--save" in args
        if save:
            print("=== DB書き込みモード（--save）===")
        else:
            print("=== ドライランモード（確認のみ）===")
        import_from_csv(save=save)
    else:
        print(__doc__)
        print("オプション:")
        print("  --export  CSVテンプレートを生成")
        print("  --import  CSVからDBにインポート")
        print("  --save    --import と組み合わせてDB書き込みを実行")
