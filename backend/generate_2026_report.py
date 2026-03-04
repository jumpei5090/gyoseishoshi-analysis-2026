
import os
import sys
import json
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from services.predictor import generate_predictions, generate_subject_predictions

def generate_full_report():
    db = SessionLocal()
    try:
        print("Calculating 2026 statistical predictions...")
        predictions = generate_predictions(db)
        subject_predictions = generate_subject_predictions(db)
        
        report_path = os.path.join(os.path.dirname(__file__), "2026_prediction_report.md")
        
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# 2026年度 行政書士試験 出題傾向 統計分析レポート\n\n")
            f.write(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("分析対象データ: 2015年〜2025年（全629問・Gemini 2.5 Flashによる高精度分類済）\n\n")
            
            f.write("## 1. 総合分析サマリー\n")
            f.write("今回の分析では、統計的な「出題周期」に加え、2026年の法改正（行政書士法改正、デジタル社会対応）による「介入効果」を数値化して算出しました。\n\n")
            
            f.write("### 分野別・ランク（激アツ順）\n")
            f.write("| ランク | 法律・分野 | 平均スコア | 最大スコア | 主要トピック |\n")
            f.write("| :--- | :--- | :---: | :---: | :--- |\n")
            for sp in subject_predictions[:10]:
                top_topic = sp["top_topics"][0]["name"] if sp["top_topics"] else "-"
                f.write(f"| {sp['rank']} | {sp['law_name']} | {sp['avg_score']} | {sp['max_score']} | {top_topic} |\n")
            f.write("\n")
            
            f.write("## 2. 激アツ！TOP 20 重要トピック（2026年度版）\n")
            f.write("以下の20項目は、過去の出題サイクルと法改正影響から、2026年度に「極めて出題可能性が高い」と判定された項目です。\n\n")
            
            for p in predictions[:20]:
                scores = p["scores"]
                f.write(f"### 第{p['rank']}位: {p['topic_name']} ({p['law_name']})\n")
                f.write(f"**総合予測スコア: {scores['composite']}%**\n\n")
                
                # 思考プロセスの要約（フルレポートから重要部分を抽出）
                full_report = scores["reasoning"].get("full_report", "")
                f.write(f"```text\n{full_report}\n```\n\n")
                
                f.write("---\n")
                
            f.write("\n## 3. 2026年特有の「改正介入」の影響について\n")
            f.write("本レポートでは、以下の項目に対して「2026年特有のブースト」をかけて計算しています。\n\n")
            f.write("- **行政書士法 (2.5x)**: 制度改革の節目であり、出題はほぼ確実視されます。\n")
            f.write("- **個人情報保護 / 情報通信 (1.3x-1.4x)**: デジタル庁主導のデジタル社会対応に伴う重要度上昇。\n")
            f.write("- **行政不服審査法 (1.25x)**: 特定行政書士の業務範囲拡大に関連。\n\n")
            
            f.write("## 4. 統計データ詳細（生データ）\n")
            f.write("| 順位 | トピック名 | 科目 | 法律 | スコア | トレンド | 周期 | 直近 | 溜め | 改正係数 |\n")
            f.write("| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
            for p in predictions[:50]:
                sc = p["scores"]
                f.write(f"| {p['rank']} | {p['topic_name']} | {p['subject_name']} | {p['law_name']} | {sc['composite']} | {sc['trend']} | {sc['cycle']} | {sc['recency']} | {sc['gap']} | {sc['intervention_boost']} |\n")
                
        print(f"Report generated: {report_path}")
        return report_path
    finally:
        db.close()

if __name__ == "__main__":
    generate_full_report()
