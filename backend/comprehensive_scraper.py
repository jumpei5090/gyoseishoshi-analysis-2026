import json
import re
import time
import urllib.request
import ssl
import os
from datetime import datetime

# Mapping of year to nendoID on goukakudojyo.com
YEAR_NENDO_MAP = {
    2015: 32, 2016: 33, 2017: 34, 2018: 35, 2019: 36,
    2020: 37, 2021: 38, 2022: 39, 2023: 40, 2024: 41, 2025: 42,
}

INDEX_URL = "https://www.pro.goukakudojyo.com/worksheet2/w_subcatnendo.php?nendoID={}"
# Main question page URL patterns
URL_PATTERNS = [
    "https://www.pro.goukakudojyo.com/worksheet2/w_mainnendo.php?queID={}",
    "https://www.pro.goukakudojyo.com/worksheet2/w_mainarch.php?queID={}"
]

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

def fetch(url, retries=3):
    """Fetch HTML content from a URL."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, context=CTX, timeout=20) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"  Error fetching {url}: {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return None

def clean_html(html):
    """Remove HTML tags and clean up whitespace."""
    if not html: return ""
    clean = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.DOTALL)
    clean = re.sub(r'<style.*?>.*?</style>', '', clean, flags=re.DOTALL)
    clean = re.sub(r'<br\s*/?>', '\n', clean)
    clean = re.sub(r'<p[^>]*>', '\n', clean)
    clean = re.sub(r'</p>', '\n', clean)
    clean = re.sub(r'<[^>]+>', '', clean)
    # Decode common HTML entities
    clean = clean.replace('&nbsp;', ' ').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"')
    return "\n".join([line.strip() for line in clean.split('\n') if line.strip()])

def parse_question_page(html):
    """Extract question text, choices, correct answer, and explanation from HTML."""
    if not html: return None
    
    data = {}
    
    # 1. Question Text
    q_match = re.search(r'id="mondai"[^>]*>(.*?)</div>', html, re.DOTALL)
    if not q_match:
        q_match = re.search(r'class="mondai"[^>]*>(.*?)</div>', html, re.DOTALL)
    
    if q_match:
        data['question_text'] = clean_html(q_match.group(1)).strip()
    
    # 2. Choices & Correct Answer
    choices = []
    correct_ans = None
    
    ans_matches = re.findall(r'SelAns\((\d+),(\d+)\)', html)
    if ans_matches:
        correct_ans = ans_matches[0][0]
        unique_choices = sorted(list(set(int(m[1]) for m in ans_matches if int(m[1]) > 0)))
        
        # Try finding choice texts in different structures
        # Structure A: <div class="sentaku_box">
        choice_texts = re.findall(r'class="sentaku_box".*?>(.*?)</div>', html, re.DOTALL)
        
        # Structure B: <table> with <td>
        if not choice_texts or len(choice_texts) < len(unique_choices):
             choice_texts = re.findall(r'<td data-title=".*?">(.*?)</td>', html, re.DOTALL)
        
        # Structure C: <li> after the label
        if not choice_texts or len(choice_texts) < len(unique_choices):
             # Some labels have text directly after them inside <li>
             choice_texts = re.findall(r'<li>\s*<input[^>]*>\s*<label[^>]*>.*?</label>\s*(.*?)\s*</li>', html, re.DOTALL)

        for i, cnum in enumerate(unique_choices):
            content = ""
            if i < len(choice_texts):
                content = clean_html(choice_texts[i]).strip()
            
            choices.append({
                "choice_number": cnum,
                "content": content,
                "is_correct": (str(cnum) == correct_ans)
            })
    
    # Fallback for choices / correct answer
    if not choices:
        choice_matches = re.findall(r'<div class="sentaku_box".*?>(.*?)</div>', html, re.DOTALL)
        for i, c_html in enumerate(choice_matches):
            choices.append({
                "choice_number": i + 1,
                "content": clean_html(c_html).strip(),
                "is_correct": False
            })

    if not correct_ans:
        ans_match = re.search(r'正解\s*(\d+)', clean_html(html))
        if ans_match:
            correct_ans = ans_match.group(1)
            for c in choices:
                if str(c['choice_number']) == correct_ans:
                    c['is_correct'] = True
    
    data['choices'] = choices
    data['correct_answer'] = correct_ans

    # 4. Explanation
    exp_match = re.search(r'class="kaisetsu"[^>]*>(.*?)</div>', html, re.DOTALL)
    if not exp_match:
        exp_match = re.search(r'id="kaisetsu"[^>]*>(.*?)</div>', html, re.DOTALL)
    
    if exp_match:
        data['explanation'] = clean_html(exp_match.group(1)).strip()
    
    return data

def main():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    seed_file = os.path.join(backend_dir, 'data', 'seed_questions.json')
    
    with open(seed_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    # Years to target: 2015 to 2024
    years = sorted(list(YEAR_NENDO_MAP.keys()))
    
    for year in years:
        nid = YEAR_NENDO_MAP[year]
        print(f"== Processing Year {year} (nendoID={nid}) ==")
        
        # 1. Fetch Index to get queIDs
        index_html = fetch(INDEX_URL.format(nid))
        if not index_html:
            print(f"  Failed to fetch index for {year}")
            continue
            
        que_matches = re.findall(r'queID=(\d+)[^>]*>[^<]*問(\d+)', index_html)
        que_map = {int(qn): int(qi) for qi, qn in que_matches}
        print(f"  Found {len(que_map)} questions in index")
        
        # 2. Fetch and parse each question
        for q_entry in [q for q in questions if q['year'] == year]:
            qnum = q_entry['question_number']
            if qnum not in que_map:
                print(f"  Question {qnum} not found in index mapping")
                continue
                
            que_id = que_map[qnum]
            print(f"  Fetching Q{qnum} (queID={que_id})...", end="", flush=True)
            
            q_html = None
            for pattern in URL_PATTERNS:
                q_html = fetch(pattern.format(que_id))
                if q_html and ("正解" in q_html or "解説" in q_html):
                    break
            
            if q_html:
                scraped = parse_question_page(q_html)
                if scraped:
                    # Update question entry
                    if 'question_text' in scraped:
                        q_entry['question_text'] = scraped['question_text']
                    if 'choices' in scraped and scraped['choices']:
                        q_entry['choices'] = scraped['choices']
                    if 'correct_answer' in scraped:
                        q_entry['correct_answer'] = scraped['correct_answer']
                    if 'explanation' in scraped:
                        q_entry['explanation'] = scraped['explanation']
                    
                    print(" Done")
                else:
                    print(" Failed to parse")
            else:
                print(" Failed to fetch")
            
            # Simple rate limiting
            time.sleep(1.2)
            
        # Periodic save after each year
        with open(seed_file, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
            
    print("\nExtraction complete. All real data merged into seed_questions.json.")

if __name__ == "__main__":
    main()
