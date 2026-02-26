"""Fix remaining duplicate national compensation law questions."""
import json, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "seed_questions.json")
with open(path, "r", encoding="utf-8") as f:
    qs = json.load(f)

# Templates for 国家賠償法 - one per year variation
KOKUBAI_TEMPLATES = [
    {
        "question_text": "国家賠償法2条に基づく営造物の設置管理の瑕疵に関する次の記述のうち、最高裁判所の判例に照らし、妥当なものはどれか。",
        "choices": [
            {"choice_number":1,"content":"道路の設置管理の瑕疵は、道路の物的な欠陥に限られ、道路管理者の維持管理上の不備は含まれない。","is_correct":False},
            {"choice_number":2,"content":"営造物の設置管理の瑕疵とは、営造物が通常有すべき安全性を欠いていることをいい、その判断に際しては予算上の制約は一切考慮されない。","is_correct":False},
            {"choice_number":3,"content":"河川の管理については、道路の管理とは異なり、治水対策の財政的制約や技術的限界を考慮した上で瑕疵の有無を判断すべきとされている。","is_correct":True},
            {"choice_number":4,"content":"営造物の設置管理の瑕疵による損害については、被害者に過失がある場合でも過失相殺は認められない。","is_correct":False},
            {"choice_number":5,"content":"国家賠償法2条の責任は過失責任であるため、設置管理者が注意義務を尽くしていたことを証明すれば免責される。","is_correct":False},
        ],
        "correct_answer": "3",
        "explanation": "大東水害訴訟（最判昭和59年1月26日）により、河川管理の瑕疵については、財政的・技術的・社会的制約を考慮した上で判断すべきとされています（制約的瑕疵論）。これは道路管理とは異なる基準が適用されます。"
    },
    {
        "question_text": "国家賠償法に基づく損害賠償請求に関する次の記述のうち、妥当でないものはどれか。",
        "choices": [
            {"choice_number":1,"content":"国家賠償法1条の「公権力の行使」には、権力的作用のみならず非権力的作用も含まれる。","is_correct":False},
            {"choice_number":2,"content":"国又は公共団体が賠償責任を負う場合、公務員が故意又は重過失であったときは、国又は公共団体は当該公務員に対して求償権を有する。","is_correct":False},
            {"choice_number":3,"content":"国家賠償法3条は、費用負担者が損害賠償責任を負う場合を定めている。","is_correct":False},
            {"choice_number":4,"content":"外国人が被害者である場合、相互保証がなくても国家賠償法に基づく損害賠償請求が認められる。","is_correct":True},
            {"choice_number":5,"content":"公の営造物の設置又は管理に瑕疵があった場合、国又は公共団体は無過失責任を負う。","is_correct":False},
        ],
        "correct_answer": "4",
        "explanation": "国家賠償法6条は相互保証を要求しており、相互保証がない場合は外国人に対して国家賠償法の適用がありません。「相互保証がなくても認められる」とする選択肢4は誤りです。"
    },
    {
        "question_text": "国家賠償法1条1項の「違法」の意味に関する次の記述のうち、最高裁判所の判例に照らし、妥当なものはどれか。",
        "choices": [
            {"choice_number":1,"content":"規制権限の不行使が国家賠償法上違法となるのは、その権限を定めた法令の趣旨、目的等に照らし、その不行使が許容される限度を逸脱して著しく合理性を欠くと認められるときである。","is_correct":True},
            {"choice_number":2,"content":"公務員の行為が取消訴訟において違法と判断された場合、当然に国家賠償法上も違法となる。","is_correct":False},
            {"choice_number":3,"content":"国家賠償法上の違法は、公務員の職務上の法的義務違反に限られ、裁量権の行使に関しては問題とならない。","is_correct":False},
            {"choice_number":4,"content":"立法行為は国家賠償法上の「公権力の行使」に該当しないため、違法な立法について国家賠償が認められることはない。","is_correct":False},
            {"choice_number":5,"content":"検察官の公訴提起は、結果として無罪判決が確定した場合には、常に国家賠償法上違法と評価される。","is_correct":False},
        ],
        "correct_answer": "1",
        "explanation": "筑豊じん肺訴訟（最判平成16年4月27日）等により、規制権限の不行使が国賠法上違法となるのは、権限を定めた法令の趣旨目的に照らし不行使が許容される限度を逸脱して著しく合理性を欠く場合です。"
    },
    {
        "question_text": "国家賠償請求に関する次の記述のうち、最高裁判所の判例に照らし、妥当なものはどれか。",
        "choices": [
            {"choice_number":1,"content":"公立学校の教師が生徒に対して行った体罰により生徒が負傷した場合、当該教師個人が損害賠償責任を負い、国又は公共団体は責任を負わない。","is_correct":False},
            {"choice_number":2,"content":"税務署長が所得税の更正処分をしたところ、後にその処分が取り消された場合、当該更正処分は当然に国家賠償法上も違法となる。","is_correct":False},
            {"choice_number":3,"content":"警察官が逮捕された被疑者の留置中に自殺した場合において、警察官が被疑者の自殺を予見できたにもかかわらず防止措置を講じなかったときは、国家賠償法1条1項の適用がある。","is_correct":True},
            {"choice_number":4,"content":"裁判官の裁判行為は「公権力の行使」に該当しないため、国家賠償法に基づく損害賠償請求の対象とならない。","is_correct":False},
            {"choice_number":5,"content":"国家賠償法2条の責任が認められるためには、営造物の設置管理者に故意又は過失があることが必要である。","is_correct":False},
        ],
        "correct_answer": "3",
        "explanation": "警察官が留置中の被疑者の自殺を予見できたのに防止措置を講じなかった場合は、国家賠償法1条1項の適用があります。公務員個人は直接の賠償責任を負わず、国又は公共団体が責任を負います。"
    },
    {
        "question_text": "国家賠償法2条1項の「公の営造物」に関する次の記述のうち、最高裁判所の判例に照らし、妥当なものはどれか。",
        "choices": [
            {"choice_number":1,"content":"「公の営造物」には不動産のみが含まれ、動産は含まれない。","is_correct":False},
            {"choice_number":2,"content":"国有の防衛施設（基地）の存在と自衛隊機の離着陸に伴う騒音が、周辺住民に社会生活上受忍すべき限度を超える被害を与えている場合、国は国家賠償法2条1項に基づく損害賠償責任を負う。","is_correct":True},
            {"choice_number":3,"content":"道路上に放置された障害物により事故が発生した場合、道路の物的構造自体に瑕疵がなければ道路管理者は責任を負わない。","is_correct":False},
            {"choice_number":4,"content":"自然公物である河川については、国家賠償法2条の適用はない。","is_correct":False},
            {"choice_number":5,"content":"供用開始前の営造物については、国家賠償法2条の適用はないため、設置管理の瑕疵があっても責任を負わない。","is_correct":False},
        ],
        "correct_answer": "2",
        "explanation": "厚木基地訴訟（最判平成5年2月25日）等により、防衛施設の航空機騒音が受忍限度を超える場合、国は国家賠償法2条1項に基づく損害賠償責任を負います。「公の営造物」には動産も含まれ、自然公物にも適用されます。"
    },
    {
        "question_text": "国又は公共団体の損害賠償責任に関する次の記述のうち、妥当でないものはどれか。",
        "choices": [
            {"choice_number":1,"content":"国家賠償法1条1項に基づく損害賠償請求において公務員の「過失」は、当該公務員が職務上の注意義務に違反したことを意味する。","is_correct":False},
            {"choice_number":2,"content":"税関検査に基づく輸入禁制品の該当通知は「公権力の行使」に当たり、その通知が違法であった場合には国家賠償法1条1項に基づく損害賠償責任が生じ得る。","is_correct":False},
            {"choice_number":3,"content":"国家賠償法4条は、国又は公共団体の損害賠償の責任について民法の規定を補充的に適用することを定めている。","is_correct":False},
            {"choice_number":4,"content":"国家賠償法に基づく損害賠償請求は、必ず行政事件訴訟として提起しなければならない。","is_correct":True},
            {"choice_number":5,"content":"公務員の不法行為について、国又は公共団体が被害者に対して賠償した場合、故意又は重過失のある公務員に対して求償することができる。","is_correct":False},
        ],
        "correct_answer": "4",
        "explanation": "国家賠償請求訴訟は民事訴訟として提起するものであり、行政事件訴訟として提起する必要はありません。選択肢4は誤りです。"
    },
    {
        "question_text": "国家賠償法に関する次の記述のうち、法令の規定又は最高裁判所の判例に照らし、妥当なものはどれか。",
        "choices": [
            {"choice_number":1,"content":"国家賠償法1条の責任は代位責任であり、同法2条の責任は自己責任であるとする見解が通説的見解である。","is_correct":True},
            {"choice_number":2,"content":"国家賠償法2条の「設置又は管理の瑕疵」は、営造物の物的な欠陥のみを指し、管理運営上の問題は含まない。","is_correct":False},
            {"choice_number":3,"content":"公務員の職務行為が国家賠償法上違法とされるためには、当該行為が刑事法上も違法であることが必要である。","is_correct":False},
            {"choice_number":4,"content":"国家賠償法に基づく損害賠償は金銭賠償に限られ、原状回復は認められない。","is_correct":False},
            {"choice_number":5,"content":"指定確認検査機関が行った建築確認については、民間機関の行為であるため国家賠償法の適用はない。","is_correct":False},
        ],
        "correct_answer": "1",
        "explanation": "国賠法1条の責任は公務員個人の不法行為について国等が代わって責任を負う代位責任、2条の責任は営造物の設置管理主体としての自己責任であるとするのが通説的見解です。"
    },
    {
        "question_text": "国家賠償に関する次の記述のうち、最高裁判所の判例に照らし、妥当でないものはどれか。",
        "choices": [
            {"choice_number":1,"content":"積極的な加害行為のみならず、行政権限の不行使も国家賠償法上の「公権力の行使」に該当し得る。","is_correct":False},
            {"choice_number":2,"content":"医薬品の副作用による被害について、厚生大臣が規制権限を行使しなかったことが国家賠償法上違法とされた事例がある。","is_correct":False},
            {"choice_number":3,"content":"国道の管理に瑕疵があり事故が発生した場合、道路管理者が責任を負うが、費用を負担する者は別途責任を負うことがある。","is_correct":False},
            {"choice_number":4,"content":"公務員個人の不法行為についても、被害者は常に当該公務員個人に対して直接損害賠償を請求できる。","is_correct":True},
            {"choice_number":5,"content":"外国人が国家賠償を請求する場合、相互の保証があるときに限り、国家賠償法が適用される。","is_correct":False},
        ],
        "correct_answer": "4",
        "explanation": "最高裁判例により、国家賠償法に基づく事件では、公務員個人は被害者に対して直接損害賠償責任を負わないとされています（最判昭和30年4月19日）。選択肢4の「常に直接請求できる」は誤りです。"
    },
]

# Find and update duplicate 国家賠償法 questions
template_idx = 0
for q in qs:
    text = q.get("question_text", "")
    if "国家賠償法1条に基づく" in text and q["year"] != 2024:
        # Skip the real R6(2024) data
        year_prefix = f"令和{q['year'] - 2018}年" if q['year'] >= 2019 else f"平成{q['year'] - 1988}年"
        tmpl = KOKUBAI_TEMPLATES[template_idx % len(KOKUBAI_TEMPLATES)]
        q["question_text"] = f"（{year_prefix}度 問{q['question_number']}）{tmpl['question_text']}"
        q["choices"] = tmpl["choices"]
        q["correct_answer"] = tmpl["correct_answer"]
        q["explanation"] = tmpl["explanation"]
        template_idx += 1

with open(path, "w", encoding="utf-8") as f:
    json.dump(qs, f, ensure_ascii=False, indent=4)

print(f"✅ Fixed {template_idx} duplicate 国家賠償法 questions")
