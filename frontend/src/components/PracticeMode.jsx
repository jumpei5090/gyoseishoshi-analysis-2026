import { useState } from 'react'
import { saveAnswer } from '../api/client'

function ChoiceButton({ choice, selected, revealed, onClick }) {
    let cls = 'practice-choice'
    if (selected) cls += ' selected'
    if (revealed) {
        if (choice.is_correct) cls += ' correct'
        else if (selected) cls += ' wrong'
        else cls += ' dimmed'
    }
    return (
        <button className={cls} onClick={onClick} disabled={revealed}>
            <span className="choice-num">{choice.choice_number}</span>
            <span className="choice-text">{choice.content}</span>
            {revealed && choice.is_correct && <span className="badge-correct">✓ 正解</span>}
        </button>
    )
}

function TashisentakuChoices({ choices, answer, setAnswer, revealed }) {
    // Multi-select: answer is an array of chosen indices for each blank
    const correctChoices = choices.filter(c => c.is_correct)
    const allChoices = choices

    return (
        <div className="tashisentaku-practice">
            <div className="tashisentaku-label">【語群から選択】</div>
            <div className="tashisentaku-grid">
                {allChoices.map((c, i) => {
                    const isSelectedCorrect = revealed && c.is_correct
                    const isSelectedWrong = revealed && answer.includes(c.choice_number) && !c.is_correct
                    let cls = 'tashisentaku-btn'
                    if (answer.includes(c.choice_number)) cls += ' selected'
                    if (revealed && c.is_correct) cls += ' correct'
                    else if (revealed && answer.includes(c.choice_number)) cls += ' wrong'
                    return (
                        <button
                            key={i}
                            className={cls}
                            disabled={revealed}
                            onClick={() => {
                                if (answer.includes(c.choice_number)) {
                                    setAnswer(answer.filter(x => x !== c.choice_number))
                                } else {
                                    setAnswer([...answer, c.choice_number])
                                }
                            }}
                        >
                            {c.content}
                        </button>
                    )
                })}
            </div>
            {revealed && (
                <div className="correct-answer-list">
                    <strong>正解の語句：</strong> {correctChoices.map(c => c.content).join('、')}
                </div>
            )}
        </div>
    )
}

function PracticeCard({ q, index, total, onNext, nickname }) {
    const [selected, setSelected] = useState(null)
    const [tashiAnswer, setTashiAnswer] = useState([])
    const [textAnswer, setTextAnswer] = useState('')
    const [revealed, setRevealed] = useState(false)

    const isKijutsu = q.format === '記述'
    const isTashi = q.format === '多肢選択'
    const isGotaku = !isKijutsu && !isTashi

    const isCorrect = isGotaku
        ? q.choices.find(c => c.choice_number === selected)?.is_correct
        : isKijutsu
            ? null  // self-assessment
            : undefined

    const handleReveal = () => {
        setRevealed(true)
        // Save to backend (skip descriptive questions)
        if (!isKijutsu && nickname) {
            let correct = false
            if (isGotaku) {
                correct = q.choices.find(c => c.choice_number === selected)?.is_correct || false
            } else if (isTashi) {
                const cNums = q.choices.filter(c => c.is_correct).map(c => c.choice_number).sort().join(',')
                const gNums = [...tashiAnswer].sort().join(',')
                correct = cNums === gNums
            }
            saveAnswer(nickname, q.id, correct, 'practice').catch(() => { })
        }
    }

    const canReveal = isKijutsu
        ? textAnswer.trim().length > 0
        : isTashi
            ? tashiAnswer.length > 0
            : selected !== null

    const resultIcon = revealed
        ? isKijutsu
            ? '📝'
            : isCorrect
                ? '⭕'
                : '❌'
        : null

    return (
        <div className="practice-card">
            {/* Progress */}
            <div className="practice-progress">
                <span className="progress-text">{index + 1} / {total}問</span>
                <div className="progress-bar-wrap">
                    <div className="progress-bar-fill" style={{ width: `${((index + 1) / total) * 100}%` }} />
                </div>
            </div>

            {/* Header */}
            <div className="practice-card-header">
                <div className="practice-meta">
                    <span className="practice-year">{q.year}年度</span>
                    <span className="practice-qnum">問{q.question_number}</span>
                    <span className="practice-format">{q.format}</span>
                </div>
                {resultIcon && (
                    <span className="practice-result-icon">{resultIcon}</span>
                )}
            </div>

            {/* Question Text */}
            <div className="practice-question-text">{q.question_text}</div>

            {/* Input Area */}
            {isGotaku && (
                <div className="practice-choices">
                    {q.choices.map((c, i) => (
                        <ChoiceButton
                            key={i}
                            choice={c}
                            selected={selected === c.choice_number}
                            revealed={revealed}
                            onClick={() => !revealed && setSelected(c.choice_number)}
                        />
                    ))}
                </div>
            )}

            {isTashi && (
                <TashisentakuChoices
                    choices={q.choices}
                    answer={tashiAnswer}
                    setAnswer={setTashiAnswer}
                    revealed={revealed}
                />
            )}

            {isKijutsu && (
                <div className="kijutsu-area">
                    <textarea
                        className="kijutsu-textarea"
                        placeholder="解答を入力してください（40〜60字程度）"
                        value={textAnswer}
                        onChange={e => setTextAnswer(e.target.value)}
                        disabled={revealed}
                        rows={4}
                    />
                    <div className="char-count">{textAnswer.length}字</div>
                </div>
            )}

            {/* Reveal Button */}
            {!revealed && (
                <button
                    className="practice-reveal-btn"
                    disabled={!canReveal}
                    onClick={handleReveal}
                >
                    {isKijutsu ? '📖 模範解答を見る' : '✅ 回答する'}
                </button>
            )}

            {/* Answer + Explanation */}
            {revealed && (
                <div className="practice-answer-section">
                    <div className={`answer-result-banner ${isKijutsu ? 'info' : isCorrect ? 'correct' : 'wrong'}`}>
                        {isKijutsu ? '📝 自己採点してください' : isCorrect ? '⭕ 正解！' : '❌ 不正解'}
                    </div>

                    {!isTashi && (
                        <div className="correct-answer-display">
                            <strong>正解：</strong>{q.correct_answer}
                        </div>
                    )}

                    {q.explanation && (
                        <div className="practice-explanation">
                            <div className="explanation-label">📖 解説</div>
                            <div className="explanation-text">{q.explanation}</div>
                        </div>
                    )}

                    <button className="practice-next-btn" onClick={onNext}>
                        {index + 1 < total ? '次の問題 →' : '✅ 完了'}
                    </button>
                </div>
            )}
        </div>
    )
}

export default function PracticeMode({ questions, onFinish, nickname }) {
    const [currentIndex, setCurrentIndex] = useState(0)
    const [done, setDone] = useState(false)

    if (questions.length === 0) {
        return (
            <div className="practice-empty">
                <div className="empty-icon">📭</div>
                <p>このトピックに問題がありません</p>
            </div>
        )
    }

    if (done) {
        return (
            <div className="practice-done">
                <div className="done-icon">🎉</div>
                <h2>練習完了！</h2>
                <p>{questions.length}問を完了しました</p>
                <button className="practice-restart-btn" onClick={() => { setCurrentIndex(0); setDone(false) }}>
                    🔄 もう一度練習する
                </button>
                <button className="practice-back-btn" onClick={onFinish}>
                    ← トピック選択に戻る
                </button>
            </div>
        )
    }

    const q = questions[currentIndex]

    return (
        <div className="practice-mode">
            <div className="practice-mode-header">
                <span className="mode-badge practice">📖 練習モード</span>
                <button className="practice-exit-btn" onClick={onFinish}>← 戻る</button>
            </div>
            <PracticeCard
                key={q.id}
                q={q}
                index={currentIndex}
                total={questions.length}
                nickname={nickname}
                onNext={() => {
                    if (currentIndex + 1 < questions.length) {
                        setCurrentIndex(currentIndex + 1)
                    } else {
                        setDone(true)
                    }
                }}
            />
        </div>
    )
}
