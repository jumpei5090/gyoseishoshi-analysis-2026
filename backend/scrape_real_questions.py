#!/usr/bin/env python3
"""
Scrape real exam questions from gyosyo.info and update seed_questions.json.
gyosyo.info URL pattern: https://gyosyo.info/exam-{era_code}-q{num:02d}.html
  era_code: r06=2024, r05=2023, r04=2022, r03=2021, r02=2020, r01=2019, h30=2018, h29=2017, h28=2016, h27=2015
"""
import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os

YEAR_TO_ERA = {
    2024: "r06", 2023: "r05", 2022: "r04", 2021: "r03", 2020: "r02",
    2019: "r01", 2018: "h30", 2017: "h29", 2016: "h28", 2015: "h27",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
}

def fetch_question_page(year, qnum):
    """Fetch a question page from gyosyo.info"""
    era = YEAR_TO_ERA[year]
    url = f"https://gyosyo.info/exam-{era}-q{qnum:02d}.html"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.text, url
    except Exception as e:
        print(f"  Error fetching {url}: {e}")
    return None, url

def parse_question_page(html):
    """Parse question text and choices from gyosyo.info HTML"""
    soup = BeautifulSoup(html, "html.parser")
    
    # Try to find the main question text
    question_text = ""
    choices = []
    
    # gyosyo.info uses various structures - try common patterns
    # Pattern 1: Look for the question content area
    content = soup.find("div", class_="entry-content") or soup.find("article") or soup.find("main")
    if not content:
        content = soup.body
    
    if not content:
        return None, None
    
    # Get all text content
    text = content.get_text(separator="\n", strip=True)
    
    # Try to extract question text (before choices)
    # Choices usually start with patterns like "1 ", "1.", "１", "ア."
    lines = text.split("\n")
    q_lines = []
    choice_lines = []
    in_choices = False
    choice_pattern = re.compile(r"^[1-5１-５]\s*[\.．\s]")
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if choice_pattern.match(line) and not in_choices:
            in_choices = True
        if in_choices:
            choice_lines.append(line)
        else:
            q_lines.append(line)
    
    if q_lines:
        # Remove navigation/header junk - take relevant content
        question_text = "\n".join(q_lines[-10:])  # Last 10 lines before choices
    
    if choice_lines:
        current_choice = ""
        for line in choice_lines:
            m = choice_pattern.match(line)
            if m:
                if current_choice:
                    choices.append(current_choice.strip())
                current_choice = line
            else:
                current_choice += " " + line
        if current_choice:
            choices.append(current_choice.strip())
    
    return question_text, choices

def try_goukakudojyo(year, qnum):
    """Try fetching from goukakudojyo.com as backup"""
    era_map = {
        2024: "reiwa6", 2023: "reiwa5", 2022: "reiwa4", 2021: "reiwa3",
        2020: "reiwa2", 2019: "reiwa1", 2018: "heisei30", 2017: "heisei29",
        2016: "heisei28", 2015: "heisei27",
    }
    era = era_map.get(year, "")
    # Try various URL patterns
    urls = [
        f"https://goukakudojyo.com/kakomondatabase/{era}-q{qnum}/",
        f"https://www.goukakudojyo.com/{era}-mon{qnum}/",
    ]
    for url in urls:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
            if resp.status_code == 200 and len(resp.text) > 1000:
                return resp.text, url
        except:
            pass
    return None, ""

def main():
    data_path = os.path.join(os.path.dirname(__file__), "data", "seed_questions.json")
    with open(data_path, "r") as f:
        questions = json.load(f)
    
    # Identify placeholder questions
    placeholders = []
    for i, q in enumerate(questions):
        txt = q.get("question_text", "")
        if len(txt) < 100 and ("に関する次の記述のうち" in txt or "当てはまる語句" in txt or "40字程度で" in txt):
            placeholders.append((i, q["year"], q["question_number"]))
    
    print(f"Found {len(placeholders)} placeholder questions to update")
    
    updated = 0
    failed = []
    
    for idx, (qi, year, qnum) in enumerate(placeholders):
        print(f"[{idx+1}/{len(placeholders)}] Fetching {year} Q{qnum}...")
        
        html, url = fetch_question_page(year, qnum)
        if not html:
            html, url = try_goukakudojyo(year, qnum)
        
        if html:
            q_text, choices = parse_question_page(html)
            if q_text and len(q_text) > 30:
                questions[qi]["question_text"] = q_text
                if choices and len(choices) >= 3:
                    # Update choices
                    existing_choices = questions[qi].get("choices", [])
                    for j, choice_text in enumerate(choices[:5]):
                        if j < len(existing_choices):
                            # Clean choice number prefix
                            clean = re.sub(r"^[1-5１-５]\s*[\.．\s]*", "", choice_text).strip()
                            existing_choices[j]["choice_text"] = clean
                    questions[qi]["choices"] = existing_choices[:len(choices)]
                updated += 1
                print(f"  ✓ Updated: {q_text[:60]}...")
            else:
                failed.append((year, qnum, url))
                print(f"  ✗ Could not parse content")
        else:
            failed.append((year, qnum, url))
            print(f"  ✗ Could not fetch page")
        
        time.sleep(0.5)  # Be polite
    
    # Save updated data
    with open(data_path, "w") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Updated: {updated}/{len(placeholders)}")
    print(f"Failed: {len(failed)}")
    if failed:
        print("\nFailed questions:")
        for y, q, u in failed[:20]:
            print(f"  {y} Q{q}: {u}")

if __name__ == "__main__":
    main()
