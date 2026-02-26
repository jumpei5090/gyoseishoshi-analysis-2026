import json
import re
import time
import urllib.request
import ssl
import os

YEAR_NENDO_MAP = {
    2015: 32, 2016: 33, 2017: 34, 2018: 35, 2019: 36,
    2020: 37, 2021: 38, 2022: 39, 2023: 40, 2024: 41,
}

INDEX_URL = "https://www.pro.goukakudojyo.com/worksheet2/w_subcatnendo.php?nendoID={}"
# Multi-choice questions can be in arch or standard
URLS = [
    "https://www.pro.goukakudojyo.com/worksheet2/w_mainnendo.php?queID={}",
    "https://www.pro.goukakudojyo.com/worksheet2/w_mainarch.php?queID={}"
]

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}

def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=CTX, timeout=15) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
    return None

def parse_tashisentaku(html):
    """Parse answer indexes and explanation for multi-choice questions."""
    # Look for patterns like ア : 8, イ : 2, ウ : 4, エ : 10
    # Sometimes it's in a table, sometimes in a list
    
    ans_map = {}
    for blank in ['ア', 'イ', 'ウ', 'エ']:
        # Match "ア[:：]\s*(\d+)"
        match = re.search(fr'{blank}\s*[:：\s]\s*(\d+)', html)
        if match:
            ans_map[blank] = int(match.group(1))
    
    # If not found by label, look for the selection circles/boxes if possible, 
    # but the label text is usually present in the revealed answer section.
    
    correct_indices = list(ans_map.values())
    correct_answer_str = ", ".join([f"{k}:{v}" for k, v in ans_map.items()])

    # Explanation
    explanation = ""
    exp_match = re.search(r'class="kaisetsu"[^>]*>(.*?)</div>', html, re.DOTALL)
    if exp_match:
        exp_html = exp_match.group(1)
        clean = re.sub(r'<p[^>]*>', '\n', exp_html)
        clean = re.sub(r'</p>', '', clean)
        clean = re.sub(r'<br\s*/?>', '\n', clean)
        clean = re.sub(r'<[^>]+>', '', clean)
        explanation = clean.strip()
    
    if not explanation and "このページの解説は公開を終了しました" in html:
        explanation = "※この問題の解説は公開を終了しています。"
        
    return correct_indices, correct_answer_str, explanation

def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    seed_file = os.path.join(backend_dir, 'data', 'seed_questions.json')

    with open(seed_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    # Multi-choice questions are Q41, 42, 43
    targets = []
    for i, q in enumerate(questions):
        if q.get('format') == '多肢選択' and 41 <= q['question_number'] <= 43:
            targets.append((i, q))

    print(f"Total multi-choice questions to update: {len(targets)}")

    # Fetch queIDs for each year
    year_que_maps = {}
    needed_years = sorted(set(q['year'] for _, q in targets))
    
    for year in needed_years:
        nid = YEAR_NENDO_MAP.get(year)
        if not nid: continue
        print(f"Fetching {year} index...")
        html = fetch(INDEX_URL.format(nid))
        if html:
            matches = re.findall(r'queID=(\d+)[^>]*>[^<]*問(\d+)', html)
            mapping = {int(qn): int(qi) for qi, qn in matches}
            year_que_maps[year] = mapping
            print(f"  Found {len(mapping)} questions")
        time.sleep(0.5)

    updated_count = 0
    for idx, (orig_idx, q) in enumerate(targets):
        year = q['year']
        qnum = q['question_number']
        
        if year not in year_que_maps or qnum not in year_que_maps[year]:
            print(f"[{idx+1}/{len(targets)}] Skip {year} Q{qnum} - no queID")
            continue
            
        que_id = year_que_maps[year][qnum]
        print(f"[{idx+1}/{len(targets)}] Fetching {year} Q{qnum} (queID={que_id})...")
        
        html = None
        for url_pattern in URLS:
            html = fetch(url_pattern.format(que_id))
            if html and "解説" in html or "正解" in html:
                break
        
        if html:
            indices, ans_str, exp = parse_tashisentaku(html)
            if indices:
                questions[orig_idx]['correct_answer'] = ans_str
                if exp:
                    questions[orig_idx]['explanation'] = exp
                
                # Update choices
                for choice in questions[orig_idx].get('choices', []):
                    if choice['choice_number'] in indices:
                        choice['is_correct'] = True
                    else:
                        choice['is_correct'] = False
                
                updated_count += 1
                print(f"  ✓ Updated. Ans: {ans_str}")
            else:
                print(f"  ✗ Failed to parse answers")
        
        time.sleep(1.0)

    # Save results
    with open(seed_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"\nFinal Results: {updated_count}/{len(targets)} questions updated.")

if __name__ == "__main__":
    main()
