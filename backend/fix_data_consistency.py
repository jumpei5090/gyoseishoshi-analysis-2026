#!/usr/bin/env python3
"""
Fix inconsistencies between correct_answer text and choice.is_correct flags.
Also attempts to fix obviously mismatched explanations.
"""
import json
import os
import re

# Load base data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "data", "seed_questions.json")

def fix_data():
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # Load official answers mapping to double-check
    try:
        from build_600_questions import ANSWERS
    except ImportError:
        # Fallback if import fails
        ANSWERS = {}

    mismatches_fixed = 0
    flags_fixed = 0
    explanations_fixed = 0

    for q in questions:
        year = q.get("year")
        qnum = q.get("question_number")
        fmt = q.get("format", "")
        correct_ans_str = str(q.get("correct_answer", ""))
        choices = q.get("choices", [])

        # Priority 1: Use ANSWERS from official source if available
        official_ans = ANSWERS.get(year, {}).get(qnum)
        
        # Decide which answer number to trust
        if official_ans is not None and official_ans > 0:
            target_num = official_ans
            if str(target_num) != correct_ans_str:
                q["correct_answer"] = str(target_num)
                mismatches_fixed += 1
        else:
            # Fallback to current correct_answer field if it's a digit
            try:
                target_num = int(re.sub(r'[^0-9]', '', correct_ans_str))
            except ValueError:
                target_num = None

        # Fix Choices is_correct flags for 5-choice selection
        if "5肢" in fmt and choices:
            if target_num is not None:
                updated = False
                for c in choices:
                    should_be = (c["choice_number"] == target_num)
                    if c.get("is_correct") != should_be:
                        c["is_correct"] = should_be
                        updated = True
                if updated:
                    flags_fixed += 1

        # Fix Multi-select (多肢選択) is_correct flags
        elif "多肢選択" in fmt and choices:
            # e.g., "ア8 イ2 ウ4 エ10"
            matches = re.findall(r'[ア-エ]([0-9]+)', correct_ans_str)
            if matches:
                correct_nums = [int(m) for m in matches]
                updated = False
                for c in choices:
                    should_be = (c["choice_number"] in correct_nums)
                    if c.get("is_correct") != should_be:
                        c["is_correct"] = should_be
                        updated = True
                if updated:
                    flags_fixed += 1

        # Fix mismatched explanations (simple keyword check)
        explanation = q.get("explanation", "")
        law = q.get("law", "")
        if explanation and law:
            # Example: 地方自治法の問題なのに、解説に「行政手続法」とだけ書いてある場合など
            if "地方自治法" in law and "行政手続法" in explanation and "地方自治法" not in explanation:
                q["explanation"] = f"{law}に関する設問です。正解は{q['correct_answer']}となります。"
                explanations_fixed += 1
            elif not explanation.strip():
                q["explanation"] = f"{law}に関する設問です。正解は選択肢{q['correct_answer']}です。"
                explanations_fixed += 1

    # Save fixed data
    with open(FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=4)

    print(f"✅ Data correction complete:")
    print(f"   - Mismatched correct_answer strings fixed: {mismatches_fixed}")
    print(f"   - Choice is_correct flags synchronized: {flags_fixed}")
    print(f"   - Explanations patched/fixed: {explanations_fixed}")

if __name__ == "__main__":
    fix_data()
