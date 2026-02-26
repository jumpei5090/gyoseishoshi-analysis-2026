import { useState, useEffect } from 'react'
import { getQuestions } from '../api/client'

function QuestionCard({ q }) {
    const [showAnswer, setShowAnswer] = useState(false)
    const isKijutsu = q.format === '記述'
    const isTashisentaku = q.format === '多肢選択'

    return (
        <div className="question-card">
            {/* Header */}
            <div className="question-header-row">
                <span className="question-number">問{q.question_number}</span>
                <span className="question-format">{q.format}</span>
            </div>
            <div className="question-meta">
                <span className="question-subject">{q.subject_name}</span>
                {q.law_name && (
                    <>
                        <span className="question-separator">›</span>
                        <span className="question-law">{q.law_name}</span>
                    </>
                )}
            </div>

            {/* Question Text */}
            {q.question_text && (
                <div className="question-text">
                    {q.question_text}
                </div>
            )}

            {/* Choices (5肢択一 / 多肢選択) */}
            {q.choices && q.choices.length > 0 && (
                <div className="question-choices">
                    {isKijutsu ? null : isTashisentaku ? (
                        <div className="tashisentaku-choices">
                            <div className="choices-label">【語群】</div>
                            {q.choices.map((c, i) => (
                                <div
                                    key={i}
                                    className={`choice-item tashisentaku-item ${showAnswer && c.is_correct ? 'correct-revealed' : ''}`}
                                >
                                    <span className="choice-content">{c.content}</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        q.choices.map((c, i) => (
                            <div
                                key={i}
                                className={`choice-item ${showAnswer ? (c.is_correct ? 'correct-revealed' : 'wrong-revealed') : ''}`}
                            >
                                <span className="choice-number-badge">{c.choice_number}</span>
                                <span className="choice-content">{c.content}</span>
                                {showAnswer && c.is_correct && (
                                    <span className="correct-badge">✓ 正解</span>
                                )}
                            </div>
                        ))
                    )}
                </div>
            )}

            {/* Answer Reveal Button */}
            {!showAnswer ? (
                <button
                    className="answer-reveal-btn"
                    onClick={() => setShowAnswer(true)}
                >
                    🔓 回答を見る
                </button>
            ) : (
                <div className="answer-section">
                    <div className="answer-header">
                        <span className="answer-badge">✅ 正解</span>
                        <span className="answer-value">{q.correct_answer}</span>
                    </div>
                    {q.explanation && (
                        <div className="explanation-box">
                            <div className="explanation-label">📖 解説</div>
                            <div className="explanation-content">{q.explanation}</div>
                        </div>
                    )}
                    <button
                        className="answer-hide-btn"
                        onClick={() => setShowAnswer(false)}
                    >
                        🔒 回答を隠す
                    </button>
                </div>
            )}

            {/* Topic Tags */}
            {q.topics.length > 0 && (
                <div className="question-topics">
                    {q.topics.map((t, i) => (
                        <span key={i} className="question-topic-tag">{t}</span>
                    ))}
                </div>
            )}
        </div>
    )
}

export default function QuestionModal({ year, keyword, onClose }) {
    const [questions, setQuestions] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        setLoading(true)
        getQuestions(keyword, year)
            .then(data => setQuestions(data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false))
    }, [year, keyword])

    // Close on Escape key
    useEffect(() => {
        const handleKey = (e) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', handleKey)
        return () => window.removeEventListener('keydown', handleKey)
    }, [onClose])

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <div>
                        <h2 className="modal-title">
                            📝 {year}年度 ─ 「{keyword}」関連の過去問
                        </h2>
                        <p className="modal-subtitle">
                            {loading ? '読み込み中...' : `${questions.length}問が該当`}
                        </p>
                    </div>
                    <button className="modal-close" onClick={onClose}>✕</button>
                </div>

                <div className="modal-body">
                    {loading ? (
                        <div className="loading">
                            <div className="spinner" />
                            問題を読み込み中...
                        </div>
                    ) : questions.length === 0 ? (
                        <div className="empty-state" style={{ padding: '32px 0' }}>
                            <div className="empty-icon">📭</div>
                            <h3>該当する問題が見つかりませんでした</h3>
                        </div>
                    ) : (
                        <div className="question-list">
                            {questions.map(q => (
                                <QuestionCard key={q.id} q={q} />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
