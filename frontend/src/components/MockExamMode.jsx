import { useState } from 'react'
import { saveAnswer } from '../api/client'

function MockQuestion({ q, index, total, userAnswer, setUserAnswer, onNext }) {
    const isKijutsu = q.format === '記述'
    const isTashi = q.format === '多肢選択'

    return (
        <div className="mock-card">
            {/* Progress */}
            <div className="practice-progress">
                <span className="progress-text">{index + 1} / {total}問</span>
                <div className="progress-bar-wrap">
                    <div className="progress-bar-fill" style={{ width: `${((index + 1) / total) * 100}%` }} />
                </div>
            </div>

            <div className="practice-card-header">
                <div className="practice-meta">
                    <span className="practice-year">{q.year}年度</span>
                    <span className="practice-qnum">問{q.question_number}</span>
                    <span className="practice-format">{q.format}</span>
                </div>
            </div>

            <div className="practice-question-text">{q.question_text}</div>

            {/* Choices */}
            {!isKijutsu && !isTashi && q.choices.map((c, i) => (
                <button
                    key={i}
                    className={`practice-choice ${userAnswer === c.choice_number ? 'selected' : ''}`}
                    onClick={() => setUserAnswer(c.choice_number)}
                >
                    <span className="choice-num">{c.choice_number}</span>
                    <span className="choice-text">{c.content}</span>
                </button>
            ))}

            {isTashi && (
                <div className="tashisentaku-practice">
                    <div className="tashisentaku-label">【語群から選択（複数可）】</div>
                    <div className="tashisentaku-grid">
                        {q.choices.map((c, i) => {
                            const arr = Array.isArray(userAnswer) ? userAnswer : []
                            const isSelected = arr.includes(c.choice_number)
                            return (
                                <button
                                    key={i}
                                    className={`tashisentaku-btn ${isSelected ? 'selected' : ''}`}
                                    onClick={() => {
                                        const arr2 = Array.isArray(userAnswer) ? [...userAnswer] : []
                                        if (isSelected) setUserAnswer(arr2.filter(x => x !== c.choice_number))
                                        else setUserAnswer([...arr2, c.choice_number])
                                    }}
                                >
                                    {c.content}
                                </button>
                            )
                        })}
                    </div>
                </div>
            )}

            {isKijutsu && (
                <div className="kijutsu-area">
                    <textarea
                        className="kijutsu-textarea"
                        placeholder="解答を入力してください（40〜60字程度）"
                        value={userAnswer || ''}
                        onChange={e => setUserAnswer(e.target.value)}
                        rows={4}
                    />
                    <div className="char-count">{(userAnswer || '').length}字</div>
                </div>
            )}

            <button
                className="practice-reveal-btn"
                onClick={onNext}
                disabled={isKijutsu ? !(userAnswer || '').trim() : isTashi ? !Array.isArray(userAnswer) || userAnswer.length === 0 : !userAnswer}
            >
                {index + 1 < total ? '次の問題 →' : '📊 結果を見る'}
            </button>
        </div>
    )
}

function ResultScreen({ questions, answers, onReview, onRestart, onFinish }) {
    const scored = questions.map((q, i) => {
        const isKijutsu = q.format === '記述'
        const isTashi = q.format === '多肢選択'
        const ans = answers[i]

        let isCorrect = null
        if (isKijutsu) {
            isCorrect = null // self-assessment only
        } else if (isTashi) {
            const correctNums = q.choices.filter(c => c.is_correct).map(c => c.choice_number).sort().join(',')
            const givenNums = (Array.isArray(ans) ? [...ans] : []).sort().join(',')
            isCorrect = correctNums === givenNums
        } else {
            isCorrect = q.choices.find(c => c.choice_number === ans)?.is_correct || false
        }

        return { q, ans, isCorrect }
    })

    const autoScorable = scored.filter(s => s.isCorrect !== null)
    const correctCount = autoScorable.filter(s => s.isCorrect).length
    const kijutsuCount = scored.filter(s => s.isCorrect === null).length
    const rate = autoScorable.length > 0
        ? Math.round((correctCount / autoScorable.length) * 100)
        : null

    return (
        <div className="mock-result">
            <h2 className="result-title">📊 結果</h2>

            <div className="result-stats">
                <div className="result-stat-card">
                    <div className="stat-label">正解数</div>
                    <div className="stat-value correct">{correctCount}<span className="stat-unit">問</span></div>
                </div>
                <div className="result-stat-card">
                    <div className="stat-label">不正解数</div>
                    <div className="stat-value wrong">{autoScorable.length - correctCount}<span className="stat-unit">問</span></div>
                </div>
                {kijutsuCount > 0 && (
                    <div className="result-stat-card">
                        <div className="stat-label">記述式（自己採点）</div>
                        <div className="stat-value info">{kijutsuCount}<span className="stat-unit">問</span></div>
                    </div>
                )}
                {rate !== null && (
                    <div className="result-stat-card highlight">
                        <div className="stat-label">正答率</div>
                        <div className="stat-value rate">{rate}<span className="stat-unit">%</span></div>
                    </div>
                )}
            </div>

            {/* Rate Bar */}
            {rate !== null && (
                <div className="rate-bar-wrap">
                    <div
                        className={`rate-bar-fill ${rate >= 60 ? 'pass' : 'fail'}`}
                        style={{ width: `${rate}%` }}
                    />
                </div>
            )}

            <div className="result-actions">
                <button className="btn-review" onClick={onReview}>📋 解説を確認する</button>
                <button className="btn-restart" onClick={onRestart}>🔄 もう一度</button>
                <button className="btn-back" onClick={onFinish}>← 戻る</button>
            </div>
        </div>
    )
}

function ReviewScreen({ questions, answers, onBack }) {
    const [expandedId, setExpandedId] = useState(null)

    const scored = questions.map((q, i) => {
        const isKijutsu = q.format === '記述'
        const isTashi = q.format === '多肢選択'
        const ans = answers[i]
        let isCorrect = null
        if (!isKijutsu) {
            if (isTashi) {
                const cNums = q.choices.filter(c => c.is_correct).map(c => c.choice_number).sort().join(',')
                const gNums = (Array.isArray(ans) ? [...ans] : []).sort().join(',')
                isCorrect = cNums === gNums
            } else {
                isCorrect = q.choices.find(c => c.choice_number === ans)?.is_correct || false
            }
        }
        return { q, ans, isCorrect }
    })

    return (
        <div className="mock-review">
            <div className="review-header">
                <h2>📋 解説確認</h2>
                <button className="btn-back" onClick={onBack}>← 結果に戻る</button>
            </div>

            {scored.map(({ q, ans, isCorrect }, i) => {
                const isOpen = expandedId === q.id
                const icon = isCorrect === null ? '📝' : isCorrect ? '⭕' : '❌'
                return (
                    <div key={q.id} className={`review-item ${isCorrect === null ? 'kijutsu' : isCorrect ? 'correct' : 'wrong'}`}>
                        <button className="review-toggle" onClick={() => setExpandedId(isOpen ? null : q.id)}>
                            <span className="review-icon">{icon}</span>
                            <span className="review-qinfo">{q.year}年度 問{q.question_number}（{q.format}）</span>
                            <span className="review-chevron">{isOpen ? '▲' : '▼'}</span>
                        </button>

                        {isOpen && (
                            <div className="review-detail">
                                <div className="practice-question-text">{q.question_text}</div>
                                {q.correct_answer && (
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
                                {isCorrect === null && (
                                    <div className="kijutsu-self-note">
                                        <strong>あなたの解答：</strong>
                                        <p>{ans || '（未入力）'}</p>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )
            })}
        </div>
    )
}

export default function MockExamMode({ questions, onFinish, nickname }) {
    const [phase, setPhase] = useState('exam') // 'exam' | 'result' | 'review'
    const [currentIndex, setCurrentIndex] = useState(0)
    const [answers, setAnswers] = useState(Array(questions.length).fill(null))
    const [currentAnswer, setCurrentAnswer] = useState(null)

    if (questions.length === 0) {
        return (
            <div className="practice-empty">
                <div className="empty-icon">📭</div>
                <p>このトピックに問題がありません</p>
            </div>
        )
    }

    const handleNext = () => {
        const newAnswers = [...answers]
        newAnswers[currentIndex] = currentAnswer
        setAnswers(newAnswers)

        if (currentIndex + 1 < questions.length) {
            setCurrentIndex(currentIndex + 1)
            setCurrentAnswer(null)
        } else {
            // Save all non-descriptive answers in bulk
            if (nickname) {
                const finalAnswers = [...newAnswers]
                questions.forEach((q, i) => {
                    if (q.format === '記述') return
                    const ans = finalAnswers[i]
                    let correct = false
                    if (q.format === '多肢選択') {
                        const cNums = q.choices.filter(c => c.is_correct).map(c => c.choice_number).sort().join(',')
                        const gNums = (Array.isArray(ans) ? [...ans] : []).sort().join(',')
                        correct = cNums === gNums
                    } else {
                        correct = q.choices.find(c => c.choice_number === ans)?.is_correct || false
                    }
                    saveAnswer(nickname, q.id, correct, 'mock').catch(() => { })
                })
            }
            setPhase('result')
        }
    }

    const handleRestart = () => {
        setPhase('exam')
        setCurrentIndex(0)
        setAnswers(Array(questions.length).fill(null))
        setCurrentAnswer(null)
    }

    if (phase === 'exam') {
        return (
            <div className="practice-mode">
                <div className="practice-mode-header">
                    <span className="mode-badge mock">📝 本番練習用モード</span>
                    <button className="practice-exit-btn" onClick={onFinish}>← 戻る</button>
                </div>
                <MockQuestion
                    key={currentIndex}
                    q={questions[currentIndex]}
                    index={currentIndex}
                    total={questions.length}
                    userAnswer={currentAnswer}
                    setUserAnswer={setCurrentAnswer}
                    onNext={handleNext}
                />
            </div>
        )
    }

    if (phase === 'result') {
        return (
            <div className="practice-mode">
                <div className="practice-mode-header">
                    <span className="mode-badge mock">📝 本番練習用モード</span>
                </div>
                <ResultScreen
                    questions={questions}
                    answers={answers}
                    onReview={() => setPhase('review')}
                    onRestart={handleRestart}
                    onFinish={onFinish}
                />
            </div>
        )
    }

    return (
        <div className="practice-mode">
            <div className="practice-mode-header">
                <span className="mode-badge mock">📝 本番練習用モード</span>
            </div>
            <ReviewScreen
                questions={questions}
                answers={answers}
                onBack={() => setPhase('result')}
            />
        </div>
    )
}
