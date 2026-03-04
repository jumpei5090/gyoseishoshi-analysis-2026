
import json
import os
import sys
from database import SessionLocal
from models import Question, Choice, Topic, Subject, Law, QuestionTopic

def load_r7():
    db = SessionLocal()
    try:
        # Check if 2025 data already exists
        ext = db.query(Question).filter(Question.year == 2025).first()
        if ext:
            print("2025 data already exists. Skipping.")
            return

        # Prepare lookup maps
        subjects = {s.name: s for s in db.query(Subject).all()}
        laws = {l.name: l for l in db.query(Law).all()}
        topics = {t.name: t for t in db.query(Topic).all()}

        # Manual mapping for R7 specificity
        SUBJECT_MAP = {
            "基礎法学": "基礎法学",
            "憲法": "憲法",
            "行政法": "行政法",
            "民法": "民法",
            "商法・会社法": "商法・会社法",
            "記述式": "行政法",  # Placeholder, will refine per question
            "多肢選択": "憲法",   # Placeholder, will refine per question
            "基礎知識": "一般知識"
        }

        r7_questions = [
            {
                "question_number": 1,
                "subject": "基礎法学",
                "law": "基礎法学",
                "format": "5肢択一",
                "topics": ["不明"],
                "question_text": "(問題文不明：著作権保護のため)",
                "choices": [],
                "correct_answer": "5",
                "explanation": "令和7年度 問1 基礎法学の問題。問題文は著作権の関係で掲載していません。正解は5です。"
            },
            {
                "question_number": 2,
                "subject": "基礎法学",
                "law": "基礎法学",
                "format": "5肢択一",
                "topics": ["裁判制度"],
                "question_text": "裁判員制度に関する次の記述のうち、裁判員法＊の規定に照らし、誤っているものはどれか。",
                "choices": [
                    {"choice_number": 1, "content": "裁判員は、衆議院議員の選挙権を有する者の中から、くじその他の作為が加わらない方法で選任される。", "is_correct": False},
                    {"choice_number": 2, "content": "一定の事由があれば、検察官、被告人または弁護人は、裁判所に対して、選任された裁判員の解任の請求をすることができる。", "is_correct": False},
                    {"choice_number": 3, "content": "裁判員は、地方裁判所で行われる一定の刑事裁判の訴訟手続に参加する。", "is_correct": False},
                    {"choice_number": 4, "content": "裁判員の関与する判断は、合議体を構成する裁判官の意見を聞いた上で、裁判員の過半数の意見によって行われる。", "is_correct": True},
                    {"choice_number": 5, "content": "裁判員が、その関与する判断のための評議の秘密を漏らしたときは、当該裁判員は、刑罰を科される。", "is_correct": False}
                ],
                "correct_answer": "4",
                "explanation": "令和7年度 問2 基礎法学の問題。正解は4です。"
            },
            {
                "question_number": 3,
                "subject": "憲法",
                "law": "憲法",
                "format": "5肢択一",
                "topics": ["法の下の平等"],
                "question_text": "法の下の平等に関する次の記述のうち、最高裁判所の判例に照らし、妥当なものはどれか。",
                "choices": [
                    {"choice_number": 1, "content": "尊属殺を通常の殺人よりも高度の道義的非難に値するものとみなし、その刑罰を通常の殺人よりも加重する規定については、社会的身分による差別を行うものとして、通常よりも厳格な基準でその合憲性が審査されなければならない。", "is_correct": False},
                    {"choice_number": 2, "content": "所得税の賦課・徴収に際して、給与所得者と自営業者等との間で異なる取り扱いを行う法律の規定については、それが人種・信条・性別など憲法 14 条 1 項の列挙する事由による差別に該当しないので、立法者の裁量を広く認めることができる。", "is_correct": False},
                    {"choice_number": 3, "content": "女性のみに再婚禁止期間を定めた民法の規定の合憲性を判断する際には、性別による差別が憲法 24 条にいう個人の尊厳と深く関わるため、性別以外による法的取り扱いの区別に比べて厳格な基準で審査が行われなければならない。", "is_correct": False},
                    {"choice_number": 4, "content": "子にとって自ら選択・修正する余地のない事柄を理由にその子に不利益を及ぼすことは許されず、子を個人として尊重し、権利を保障すべきだという考えが確立されてきており、嫡出でない子の法定相続分を差別する規定の合理性は失われている。", "is_correct": True},
                    {"choice_number": 5, "content": "憲法 25 条の定める生存権は個人の尊厳と密接に関係する権利であり、これに関係する法的取り扱いの区別の合憲性については、立法者がその裁量を踰越していな いか厳格かつ慎重に審査されなければならない。", "is_correct": False}
                ],
                "correct_answer": "4",
                "explanation": "令和7年度 問3 憲法の問題。正解は4です。最大判平成25.9.4（非嫡出子相続分違憲決定）は、嫡出でない子の法定相続分を差別する規定の合理性は失われているとしています。"
            },
            {
                "question_number": 4,
                "subject": "憲法",
                "law": "憲法",
                "format": "5肢択一",
                "topics": ["精神的自由"],
                "question_text": "取材・報道の自由に関する次の記述のうち、最高裁判所の判例に照らし、妥当でないものはどれか。",
                "choices": [
                    {"choice_number": 1, "content": "公正な刑事裁判の実現を保障するために、報道機関の取材活動によって得られたものが証拠として必要と認められるような場合には、取材の自由がある程度の制約をこうむることとなってもやむを得ない。", "is_correct": False},
                    {"choice_number": 2, "content": "報道機関の取材の手段・方法が一般の刑罰法令に触れなくても、取材対象者の個人としての人格の尊厳を著しく蹂躪する等、法秩序全体の精神に照らし社会観念上是認できない態様である場合には、正当な取材活動の範囲を逸脱する。", "is_correct": False},
                    {"choice_number": 3, "content": "不法行為の成立を前提としない反論権は、特に公的事項に関する批判的記事の掲載をちゅうちょさせ、憲法が保障する表現の自由を間接的に侵す危険につながるおそれも多分に存し、当然に認められるものではない。", "is_correct": False},
                    {"choice_number": 4, "content": "報道の公共性、報道のための取材の自由に対する配慮に基づき、司法記者クラブ所属の報道機関の記者に対してのみ法廷におけるメモの採取を許可したとしても、法の下の平等には反しない。", "is_correct": False},
                    {"choice_number": 5, "content": "報道関係者の取材源は、それがみだりに開示されると将来の自由で円滑な取材活動に一定の支障は生じうるが、公正な裁判の実現のためには取材源を明らかにする必要があり、民事訴訟法上の証言拒絶が認められうる職業の秘密には該当しない。", "is_correct": True}
                ],
                "correct_answer": "5",
                "explanation": "令和7年度 問4 憲法の問題。正解は5です。最閉平成18.10.3（石井記者事件）では、取材源の秘匿は、民事訴訟法上の「職業の秘密」として、一定の要件を満たせば証言拒絶が認められうるとしています。"
            },
            {
                "question_number": 5,
                "subject": "憲法",
                "law": "憲法",
                "format": "5肢択一",
                "topics": ["国会"],
                "question_text": "国会の召集に関する次の文章の空欄 ア 〜 エ に当てはまる語句の組合せとして、妥当なものはどれか。",
                "choices": [
                    {"choice_number": 1, "content": "ア：会期　イ：特別　ウ：臨時　エ：権限又は権能", "is_correct": False},
                    {"choice_number": 2, "content": "ア：立法期　イ：臨時　ウ：特別　エ：権限又は権能", "is_correct": False},
                    {"choice_number": 3, "content": "ア：会期　イ：特別　ウ：臨時　エ：権利又は利益", "is_correct": False},
                    {"choice_number": 4, "content": "ア：立法期　イ：特別　ウ：臨時　エ：権限又は権能", "is_correct": False},
                    {"choice_number": 5, "content": "ア：会期　イ：臨時　ウ：特別　エ：権利又は利益", "is_correct": True}
                ],
                "correct_answer": "5",
                "explanation": "令和7年度 問5 憲法の問題。正解は5です。最三小判令和5.9.12（那覇臨時国会召集要求訴訟）の判旨に基づいています。"
            },
            {
                "question_number": 8,
                "subject": "行政法",
                "law": "行政法総論",
                "format": "5肢択一",
                "topics": ["行政行為"],
                "question_text": "行政行為（処分）に関する次の記述のうち、最高裁判所の判例に照らし、妥当なものはどれか。",
                "choices": [
                    {"choice_number": 1, "content": "瑕疵なく成立した授益的処分について、事後の事情の変化を理由に講学上の撤回をすることは、かかる撤回ができる旨を定める明文の規定が法律または条例にあるときに限られる。", "is_correct": False},
                    {"choice_number": 2, "content": "重大かつ明白な瑕疵を有する処分は当然に無効とされるが、処分の瑕疵が明白であるかどうかは、処分の外形上、客観的に誤認が一見看取し得るものであるかどうかに決まる。", "is_correct": True},
                    {"choice_number": 3, "content": "一定の争訟手続に従って当事者を手続に関与せしめ、紛争の終局的解決を図ることを目的とする処分であっても、当該処分をした行政庁は、特別の規定がない限り、当該処分を取り消すことができる。", "is_correct": False},
                    {"choice_number": 4, "content": "既になされた授益的処分について、講学上の職権取消しができるのは、当該授益的処分の成立時に違法があるときに限られ、不当があるにすぎない場合は除外される。", "is_correct": False},
                    {"choice_number": 5, "content": "処分の成立時点において瑕疵があった場合、事後の事情の変化により当該瑕疵が解消するに至ったとしても、その瑕疵は治癒されることはなく、当該処分はそれを理由として取り消されるか、または当然に無効であるとされる。", "is_correct": False}
                ],
                "correct_answer": "2",
                "explanation": "令和7年度 問8 行政法の問題。正解は2です。判例（最判昭和36.3.7など）は、瑕疵の明白性について、一見看取し得るものであるかどうかにより決まるとしています。"
            },
            {
                "question_number": 11,
                "subject": "行政法",
                "law": "行政手続法",
                "format": "5肢択一",
                "topics": ["申請に対する処分"],
                "question_text": "行政手続法が定める弁明の機会の付与に関する次の記述のうち、妥当なものはどれか。",
                "choices": [
                    {"choice_number": 1, "content": "不利益処分の名宛人となるべき者として弁明の機会の付与の通知を受けた者は、代理人を選任することができる。", "is_correct": True},
                    {"choice_number": 2, "content": "不利益処分の名宛人となるべき者として弁明の機会の付与の通知を受けた者は、行政庁に対し、弁明を記載した書面（弁明書）を提出する時までの間、当該不利益処分の原因となる事実を証する資料の閲覧を求めることができる。", "is_correct": False},
                    {"choice_number": 3, "content": "弁明を記載した書面（弁明書）が提出された後、当該不利益処分に利害関係を有する者が当該弁明書の閲覧を求めた場合、行政庁は、正当な理由があるときでなければ、その閲覧を拒むことができない。", "is_correct": False},
                    {"choice_number": 4, "content": "弁明を記載した書面（弁明書）の提出を受けた行政庁は、当該弁明についての調書及び報告書を作成しなければならない。", "is_correct": False},
                    {"choice_number": 5, "content": "行政庁は、弁明を記載した書面（弁明書）が提出された後に新たな事情が生じたときは、弁明書を提出した者に対しその再提出を求めなければならない。", "is_correct": False}
                ],
                "correct_answer": "1",
                "explanation": "令和7年度 問11 行政法の問題。正解は1です。行政手続法31条により、弁明の機会の付与においても、16条（代理人）の規定が準用されています。"
            },
            {
                "question_number": 44,
                "subject": "行政法",
                "law": "行政不服審査法",
                "format": "記述",
                "topics": ["裁決"],
                "question_text": "議事に加わった委員の一人が利害関係を有する者であるという手続上の瑕疵に対し、誰を被告としてどのような抗告訴訟を提起すべきか。",
                "choices": [],
                "correct_answer": "裁決の固有の瑕疵を主張して、Ｙ市を被告として、裁決取消訴訟を提起すべきである。",
                "explanation": "令和7年度 問44 記述式の問題。裁決に固有の瑕疵（除斥事由違反）があるため、裁決の取消しを求める訴えを提起します。"
            },
            {
                "question_number": 45,
                "subject": "民法",
                "law": "民法総則",
                "format": "記述",
                "topics": ["代理"],
                "question_text": "夫婦の一方が他方の代理人と称して法律行為をした場合における、民法110条の類推適用の要件につき記述しなさい。",
                "choices": [],
                "correct_answer": "Ｃにおいて、Ｂにその権限があると信ずべき正当な理由があるときに類推適用を認めている。",
                "explanation": "令和7年度 問45 記述式の問題。判例（最判昭和44.12.18）に基づきます。"
            },
            {
                "question_number": 46,
                "subject": "民法",
                "law": "債権各論",
                "format": "記述",
                "topics": ["事務管理"],
                "question_text": "消防署に通報し消火活動を開始した場合、どのような法的根拠に基づき継続し、消火器費用をどのような性質のものとして請求できるか。",
                "choices": [],
                "correct_answer": "事務管理に基づき継続し、その費用を、有益費の償還としてＢに対して請求することができる。",
                "explanation": "令和7年度 問46 記述式の問題。民法697条（事務管理）および702条（有益費償還請求）に関わります。"
            },
            {
                "question_number": 57,
                "subject": "一般知識",
                "law": "一般知識",
                "format": "5肢択一",
                "topics": ["情報通信"],
                "question_text": "個人情報保護制度に関する次の記述のうち、妥当なものはどれか。",
                "choices": [
                    {"choice_number": 1, "content": "個人情報保護法＊では、民間事業者への罰則として、年間の売上高に応じた額を上限とした罰金が定められている。", "is_correct": False},
                    {"choice_number": 2, "content": "個人情報保護法には、刑事罰としての罰金以外に、制定時以来、課徴金が定められている。", "is_correct": False},
                    {"choice_number": 3, "content": "個人情報保護委員会は、いわゆるマイナンバーカード（個人番号カード）の交付事務を行っている。", "is_correct": False},
                    {"choice_number": 4, "content": "個人情報保護委員会は、個人情報保護法の定める行政機関等に対しては監視を行わない。", "is_correct": False},
                    {"choice_number": 5, "content": "個人情報保護委員会は、個人情報保護法の定める個人情報取扱事業者等に対して立入検査を行うことができる。", "is_correct": True}
                ],
                "correct_answer": "5",
                "explanation": "令和7年度 問57 基礎知識（個人情報保護法）の問題。正解は5です。"
            },
            {
                "question_number": 58,
                "subject": "一般知識",
                "law": "一般知識",
                "format": "5肢択一",
                "topics": ["文章理解"],
                "question_text": "(問題文不明：著作権保護のため)",
                "choices": [],
                "correct_answer": "2",
                "explanation": "令和7年度 問58 文章理解の問題。問題文は著作権の関係で掲載していません。正解は2です。"
            },
            {
                "question_number": 59,
                "subject": "一般知識",
                "law": "一般知識",
                "format": "5肢択一",
                "topics": ["文章理解"],
                "question_text": "(問題文不明：著作権保護のため)",
                "choices": [],
                "correct_answer": "4",
                "explanation": "令和7年度 問59 文章理解の問題。問題文は著作権の関係で掲載していません。正解は4です。"
            },
            {
                "question_number": 60,
                "subject": "一般知識",
                "law": "一般知識",
                "format": "5肢択一",
                "topics": ["文章理解"],
                "question_text": "(問題文不明：著作権保護のため)",
                "choices": [],
                "correct_answer": "3",
                "explanation": "令和7年度 問60 文章理解の問題。問題文は著作権の関係で掲載していません。正解は3です。"
            }
        ]

        # Official answer map for others
        ans_map = {
            1: "5", 6: "2", 7: "2", 9: "1", 10: "1", 12: "4", 13: "3", 14: "1", 15: "3", 16: "5",
            17: "1", 18: "5", 19: "3", 20: "4", 21: "4", 22: "5", 23: "2", 24: "2", 25: "3", 26: "4",
            27: "3", 28: "4", 29: "5", 30: "2", 31: "4", 32: "2", 33: "3", 34: "4", 35: "3", 36: "1",
            37: "5", 38: "2", 39: "4", 40: "4", 41: "1", 42: "1", 43: "1", # Multi-choice placeholders
            47: "2", 48: "4", 49: "3", 50: "2", 51: "3", 52: "5", 53: "5", 54: "2", 55: "3", 56: "1"
        }

        # Fill missing questions with defaults or brief info
        for q_num in range(1, 61):
            if any(q["question_number"] == q_num for q in r7_questions):
                continue
            
            # Subject/Law logic for Reiwa 7
            if 1 <= q_num <= 2: subject, law = "基礎法学", "基礎法学"
            elif 3 <= q_num <= 7: subject, law = "憲法", "憲法"
            elif 8 <= q_num <= 26: 
                subject, law = "行政法", "行政法総論"
                if 11 <= q_num <= 13: law = "行政手続法"
                elif 14 <= q_num <= 16: law = "行政不服審査法"
                elif 17 <= q_num <= 19: law = "行政事件訴訟法"
                elif 20 <= q_num <= 21: law = "国家賠償法"
                elif 22 <= q_num <= 24: law = "地方自治法"
            elif 27 <= q_num <= 35:
                subject, law = "民法", "民法総則"
                if 29 <= q_num <= 30: law = "物権法"
                elif 31 <= q_num <= 32: law = "債権総論"
                elif 33 <= q_num <= 34: law = "債権各論"
                elif q_num == 35: law = "親族法・相続法"
            elif 36 <= q_num <= 40:
                subject, law = "商法・会社法", "商法" if q_num == 36 else "会社法"
            elif 41 <= q_num <= 43:
                subject, law = "憲法" if q_num == 41 else "行政法", "憲法" if q_num == 41 else "行政法総論"
            elif 44 <= q_num <= 46:
                subject, law = ("行政法", "行政不服審査法") if q_num == 44 else ("民法", "民法総則")
            else:
                subject, law = "一般知識", "一般知識"

            r7_questions.append({
                "question_number": q_num,
                "subject": subject,
                "law": law,
                "format": "記述" if 44 <= q_num <= 46 else "多肢選択" if 41 <= q_num <= 43 else "5肢択一",
                "topics": ["不明" if q_num in [1, 58, 59, 60] else "その他"],
                "question_text": f"令和7年度 問{q_num} 問題文(準備中)",
                "choices": [],
                "correct_answer": ans_map.get(q_num, "1"),
                "explanation": f"令和7年度 問{q_num}の解析データです。"
            })

        # DB Mapping
        subjects_db = {s.name: s for s in db.query(Subject).all()}
        laws_db = {l.name: l for l in db.query(Law).all()}
        topics_db = {t.name: t for t in db.query(Topic).all()}

        for q_data in r7_questions:
            subject = subjects_db.get(q_data["subject"])
            law = laws_db.get(q_data["law"])
            
            if not subject:
                print(f"Warning: Subject {q_data['subject']} not found for Q{q_data['question_number']}")
                continue

            q = Question(
                year=2025,
                question_number=q_data["question_number"],
                subject_id=subject.id,
                law_id=law.id if law else None,
                question_format=q_data["format"],
                question_text=q_data["question_text"],
                correct_answer=q_data["correct_answer"],
                explanation=q_data["explanation"]
            )
            db.add(q)
            db.flush()
            
            for c_data in q_data.get("choices", []):
                db.add(Choice(
                    question_id=q.id,
                    choice_number=c_data["choice_number"],
                    content=c_data["content"],
                    is_correct=c_data.get("is_correct", False)
                ))
            
            for topic_name in q_data["topics"]:
                topic = topics_db.get(topic_name)
                if not topic and law:
                    # Generic topic per law
                    topic = db.query(Topic).filter(Topic.law_id == law.id).first()
                
                if topic:
                    db.add(QuestionTopic(question_id=q.id, topic_id=topic.id))
        
        db.commit()
        print("Successfully loaded 2025 questions.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    load_r7()
