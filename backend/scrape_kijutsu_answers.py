import json
import re
import time
import urllib.request
import ssl
import os

# Year to nendoID mapping
YEAR_NENDO_MAP = {
    2015: 32, 2016: 33, 2017: 34, 2018: 35, 2019: 36,
    2020: 37, 2021: 38, 2022: 39, 2023: 40, 2024: 41,
}

INDEX_URL = "https://www.pro.goukakudojyo.com/worksheet2/w_subcatnendo.php?nendoID={}"
QUESTION_URL = "https://www.pro.goukakudojyo.com/worksheet2/w_mainnendo.php?queID={}"

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

def parse_kijutsu(html):
    """Parse model answer and explanation for kijutsu questions."""
    # Correct Answer Example (正解例 / 当時の正解例 / 試験センターの解答例)
    # Priority:
    # 1. ■試験センターの解答例 (Found in some years)
    # 2. 正解例 / 当時の正解例
    
    correct_answer = ""
    
    # Try finding exam center examples first
    center_match = re.search(r'■試験センターの解答例(.*?)(?:<div|class="kaisetsu"|class="tit"|$)', html, re.DOTALL)
    if center_match:
        content = center_match.group(1)
        examples = re.findall(r'【例\d+】(.*?)(?:【|（\d+字）|$)', content, re.DOTALL)
        if examples:
            correct_answer = "\n".join([f"例{i+1}: {e.strip()}" for i, e in enumerate(examples)])
    
    if not correct_answer:
        # Standard positive answer or archived answer
        ca_match = re.search(r'(?:正解例|当時の正解例).*?<strong>(.*?)</strong>', html, re.DOTALL)
        if not ca_match:
            # Another variant: wrapped in a div/p without strong
            ca_match = re.search(r'class="kotae"[^>]*>(.*?)<', html, re.DOTALL)
            
        if ca_match:
            correct_answer = re.sub(r'<[^>]+>', '', ca_match.group(1)).strip()
            # Clean up prefixes if they matched
            correct_answer = re.sub(r'^(?:正解例|当時の正解例)\s*', '', correct_answer)

    # Explanation (解説)
    # <div class="kaisetsu">(.*?)</div> or following "解説" header
    explanation = ""
    exp_match = re.search(r'class="kaisetsu"[^>]*>(.*?)</div>', html, re.DOTALL)
    if exp_match:
        exp_html = exp_match.group(1)
        clean = re.sub(r'<p[^>]*>', '\n', exp_html)
        clean = re.sub(r'</p>', '', clean)
        clean = re.sub(r'<br\s*/?>', '\n', clean)
        clean = re.sub(r'<[^>]+>', '', clean)
        explanation = clean.strip()
    
    if not explanation:
        # Check for archive notice
        if "このページの解説は公開を終了しました" in html:
            explanation = "※この問題の解説は公開を終了しています。"
            
    return correct_answer, explanation

def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    seed_file = os.path.join(backend_dir, 'data', 'seed_questions.json')

    with open(seed_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    # Descriptive questions are Q44, 45, 46 from 2015-2024
    targets = []
    for i, q in enumerate(questions):
        if q.get('format') == '記述' and 44 <= q['question_number'] <= 46:
            targets.append((i, q))

    print(f"Total descriptive questions to check: {len(targets)}")

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
        
        html = fetch(QUESTION_URL.format(que_id))
        if html:
            ans, exp = parse_kijutsu(html)
            if ans and len(ans) > 5:
                questions[orig_idx]['correct_answer'] = ans
                if exp:
                    questions[orig_idx]['explanation'] = exp
                updated_count += 1
                print(f"  ✓ Updated. Ans: {ans[:30]}...")
            else:
                print(f"  ✗ Failed to parse answer")
        
        time.sleep(1.0)

    # Save results
    with open(seed_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"\nFinal Results: {updated_count}/{len(targets)} questions updated.")

if __name__ == "__main__":
    main()
