
import json
import re

# User provided text (truncated/simplified for parsing logic)
# I will use the actual text from the user's message in a real scenario
# But here I'll write the script and then I'll feed the text to it or just simulate it.

def parse_questions(text):
    questions = []
    # Split by "問題" followed by a number
    parts = re.split(r'問題\s?(\d+)\s+', text)
    
    # parts[0] is preamble
    for i in range(1, len(parts), 2):
        q_num = int(parts[i])
        content = parts[i+1]
        
        # Split content into question text and choices
        # Choices usually start with "1 ", "2 ", etc.
        choice_parts = re.split(r'\n([1-5])\s+', content)
        
        q_text = choice_parts[0].strip()
        choices = []
        for j in range(1, len(choice_parts), 2):
            c_num = int(choice_parts[j])
            c_text = choice_parts[j+1].split('\n')[0].strip() # Get only the first line of the choice
            choices.append({
                "choice_number": c_num,
                "content": c_text
            })
        
        questions.append({
            "question_number": q_num,
            "question_text": q_text,
            "choices": choices
        })
    return questions

# I'll actually manually curate Question 2-46 for better precision since the format varies (Multi-choice, Descriptive)
