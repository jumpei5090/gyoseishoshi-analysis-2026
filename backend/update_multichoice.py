# -*- coding: utf-8 -*-
import json

# Load HTTP scrape results
with open('multchoice_scrape.json', 'r', encoding='utf-8') as f:
    scraped = json.load(f)

# Load 2021 manual data
with open('manual_2021.json', 'r', encoding='utf-8') as f:
    manual = json.load(f)

# Build map
scraped_map = {}
for s in scraped:
    scraped_map[(s['year'], s['qn'])] = s
for m in manual:
    scraped_map[(m['year'], m['qn'])] = m

print(f"Total scraped multi-choice: {len(scraped_map)}")

# Load seed data
with open('data/seed_questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

updated = 0
for q in data:
    y = q['year']
    qn = q['question_number']
    
    if (y, qn) in scraped_map:
        s = scraped_map[(y, qn)]
        new_text = s['text']
        new_choices = s['choices']
        
        if len(new_choices) != 20:
            continue
        
        old_text = q.get('question_text', '')
        old_choices = q.get('choices', [])
        
        # Update text and choices
        q['question_text'] = new_text
        q['format'] = u'多肢選択'
        q['choices'] = [{'choice_number': c['choice_number'], 'content': c['content'], 'is_correct': False} for c in new_choices]
        updated += 1
        print(f"  {y} Q{qn}: text {len(old_text)}->{len(new_text)}, choices {len(old_choices)}->{len(new_choices)}")

# Also fix 2024 Q23-25: they are NOT multi-choice, they are 5肢択一
for qn in [23, 24, 25]:
    for q in data:
        if q['year'] == 2024 and q['question_number'] == qn:
            if q.get('format') == u'多肢選択':
                q['format'] = u'5肢択一'
                print(f"  2024 Q{qn}: multi-choice -> 5-choice (has 'doreka' in text)")
                updated += 1

# Save
with open('data/seed_questions.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\nTotal updates: {updated}")

# Format distribution
formats = {}
for q in data:
    fmt = q.get('format', '')
    formats[fmt] = formats.get(fmt, 0) + 1
for f, c in sorted(formats.items()):
    print(f"  {f}: {c}")
