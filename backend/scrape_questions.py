"""
Scrape real question data from goukakudojyo.com to fix placeholder questions.
"""
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

BASE_URL_ARCH = "https://www.pro.goukakudojyo.com/worksheet2/w_mainarch.php?queID={}"
BASE_URL_NENDO = "https://www.pro.goukakudojyo.com/worksheet2/w_mainnendo.php?queID={}"
INDEX_URL = "https://www.pro.goukakudojyo.com/worksheet2/w_subcatnendo.php?nendoID={}"

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


def parse_question(html):
    """Parse question from goukakudojyo.com HTML."""
    result = {'question_text': '', 'choices': [], 'correct_answer': ''}

    # ==== Question text ====
    # Find content in <div class="toi">
    toi = re.search(r'class="toi">(.*?)</div>\s*</div>', html, re.DOTALL)
    if not toi:
        toi = re.search(r'class="toi">(.*?)</div>', html, re.DOTALL)
    if toi:
        content = toi.group(1)
        # Question text is in <p> tags before <ol>
        before_ol = re.split(r'<ol', content)[0]
        p_texts = re.findall(r'<p[^>]*>(.*?)</p>', before_ol, re.DOTALL)
        q_parts = []
        for p in p_texts:
            clean = re.sub(r'<br\s*/?>', '\n', p)
            clean = re.sub(r'<[^>]+>', '', clean).strip()
            if clean:
                q_parts.append(clean)
        result['question_text'] = '\n'.join(q_parts)

    # ==== Choices ====
    # Method 1: <ol><li> structure
    mondai = re.search(r'class="mondai-wrap">(.*?)class="kekka"', html, re.DOTALL)
    if not mondai:
        mondai = re.search(r'class="mondai-wrap">(.*?)$', html, re.DOTALL)
    
    if mondai:
        mc = mondai.group(1)
        ol_match = re.search(r'<ol[^>]*>(.*?)</ol>', mc, re.DOTALL)
        if ol_match:
            ol_content = ol_match.group(1)
            # Split by <li> tags
            li_parts = re.split(r'<li[^>]*>', ol_content)
            for i, part in enumerate(li_parts[1:], 1):  # skip first empty
                # Remove radio buttons and other control spans
                clean = re.sub(r'<span\s+class="SlctChk".*?</span>', '', part, flags=re.DOTALL)
                # Remove any remaining tags
                clean = re.sub(r'<br\s*/?>', '\n', clean)
                clean = re.sub(r'<[^>]+>', '', clean)
                clean = clean.strip()
                # Remove trailing "SlctChk" artifacts
                clean = re.sub(r'\s*SlctChk.*$', '', clean, flags=re.DOTALL)
                if clean:
                    result['choices'].append({'choice_number': i, 'content': clean})

    # Method 2: Table-based choices (組合せ問題)
    if not result['choices'] and mondai:
        mc = mondai.group(1)
        # Look for table with choices
        table_match = re.search(r'<table[^>]*class="[^"]*sentaku[^"]*"[^>]*>(.*?)</table>', mc, re.DOTALL)
        if table_match:
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', table_match.group(1), re.DOTALL)
            for i, row in enumerate(rows[1:], 1):  # skip header
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                if cells:
                    content_parts = []
                    for cell in cells:
                        clean = re.sub(r'<[^>]+>', '', cell).strip()
                        if clean:
                            content_parts.append(clean)
                    if content_parts:
                        # First cell is usually the choice number
                        choice_content = ' '.join(content_parts[1:]) if len(content_parts) > 1 else content_parts[0]
                        result['choices'].append({'choice_number': i, 'content': choice_content})

    # ==== Correct answer ====
    # Archive format: 当時の答え<span class="arch-ans">N</span>
    ans = re.search(r'class="arch-ans"[^>]*>\s*(\d+)', html)
    if ans:
        result['correct_answer'] = ans.group(1)
    else:
        # Recent format: <p class="kotae">正解<strong>N</strong>
        ans = re.search(r'class="kotae"[^>]*>.*?<strong>\s*(\d+)', html, re.DOTALL)
        if ans:
            result['correct_answer'] = ans.group(1)
        else:
            # Fallback
            ans = re.search(r'(?:当時の)?(?:正解|答え)\s*[：:]?\s*(\d+)', html)
            if ans:
                result['correct_answer'] = ans.group(1)

    return result


def main():
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    seed_file = os.path.join(data_dir, 'seed_questions.json')

    with open(seed_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    # Find placeholder questions
    placeholders = []
    for i, q in enumerate(questions):
        choices = q.get('choices', [])
        if choices:
            first = choices[0].get('content', '')
            if '選択肢' in first and ('平成' in first or '令和' in first):
                placeholders.append((i, q))
        elif not choices:
            placeholders.append((i, q))

    print(f"Placeholder questions to fix: {len(placeholders)}")

    # Step 1: Build queID mappings for all years
    needed_years = sorted(set(q['year'] for _, q in placeholders))
    print(f"Years: {needed_years}")

    year_que_maps = {}
    for year in needed_years:
        nid = YEAR_NENDO_MAP.get(year)
        if not nid:
            continue
        print(f"  Fetching {year} index (nendoID={nid})...")
        html = fetch(INDEX_URL.format(nid))
        if html:
            matches = re.findall(r'queID=(\d+)[^>]*>[^<]*問(\d+)', html)
            mapping = {int(qn): int(qi) for qi, qn in matches}
            year_que_maps[year] = mapping
            print(f"    {len(mapping)} questions mapped")
        time.sleep(0.5)

    # Step 2: Scrape each placeholder question
    updated = 0
    failed = 0
    failed_list = []

    for idx, (orig_idx, q) in enumerate(placeholders):
        year = q['year']
        qnum = q['question_number']

        if year not in year_que_maps or qnum not in year_que_maps[year]:
            print(f"  [{idx+1}/{len(placeholders)}] SKIP {year} Q{qnum} — no queID")
            failed += 1
            failed_list.append(f"{year}-Q{qnum}")
            continue

        que_id = year_que_maps[year][qnum]

        # Try both URL formats
        urls = [
            BASE_URL_ARCH.format(que_id),
            BASE_URL_NENDO.format(que_id),
        ]

        parsed = None
        for url in urls:
            html = fetch(url)
            if html and ('mondai' in html or 'toi' in html):
                parsed = parse_question(html)
                if parsed['choices']:
                    break
            time.sleep(0.3)

        if parsed and parsed['choices']:
            questions[orig_idx]['choices'] = parsed['choices']
            if parsed['correct_answer']:
                questions[orig_idx]['correct_answer'] = parsed['correct_answer']
            if parsed['question_text'] and len(parsed['question_text']) > 10:
                questions[orig_idx]['question_text'] = parsed['question_text']
            updated += 1
            nc = len(parsed['choices'])
            print(f"  [{idx+1}/{len(placeholders)}] ✓ {year} Q{qnum}: {nc} choices, ans={parsed['correct_answer']}")
        else:
            failed += 1
            failed_list.append(f"{year}-Q{qnum}")
            print(f"  [{idx+1}/{len(placeholders)}] ✗ {year} Q{qnum}: parse failed")

        time.sleep(0.8)

        # Progress save every 30 questions
        if (idx + 1) % 30 == 0:
            with open(os.path.join(data_dir, 'seed_questions_progress.json'), 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            print(f"  ... Progress: {updated} updated, {failed} failed")

    # Final save
    print(f"\n=== RESULTS ===")
    print(f"Updated: {updated}/{len(placeholders)}")
    print(f"Failed: {failed}")
    if failed_list:
        print(f"Failed questions: {failed_list[:20]}{'...' if len(failed_list) > 20 else ''}")

    with open(seed_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print(f"Saved to {seed_file}")


if __name__ == '__main__':
    main()
