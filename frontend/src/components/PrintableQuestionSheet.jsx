import React from 'react'

export default function PrintableQuestionSheet({ questions, subjectName, lawName, topicName }) {
    if (!questions || questions.length === 0) return null

    return (
        <div className="printable-sheet">
            <header className="print-header">
                <h1>行政書士試験 過去問演習シート</h1>
                <div className="print-metadata">
                    <span className="print-breadcrumb">
                        {subjectName} › {lawName} › <strong>{topicName}</strong>
                    </span>
                    <span className="print-count">{questions.length}問</span>
                </div>
            </header>

            <section className="print-questions-section">
                {questions.map((q, index) => (
                    <div key={q.id} className="print-question-card">
                        <div className="print-q-header">
                            <span className="print-q-num">第 {index + 1} 問</span>
                            <span className="print-q-meta">({q.year}年度 問{q.question_number} / {q.format})</span>
                        </div>
                        <div className="print-q-text">{q.question_text}</div>

                        {q.format !== '記述' && q.choices && q.choices.length > 0 && (
                            <div className="print-choices">
                                {q.choices.map((c) => (
                                    <div key={c.choice_number} className="print-choice-item">
                                        {c.choice_number}. {c.content}
                                    </div>
                                ))}
                            </div>
                        )}

                        {q.format === '記述' && (
                            <div className="print-kijutsu-box">
                                {/* Answer box for descriptive questions */}
                                <div className="print-kijutsu-grid">
                                    {[...Array(60)].map((_, i) => (
                                        <div key={i} className="print-grid-cell"></div>
                                    ))}
                                </div>
                                <div className="print-kijutsu-hint">（40字〜60字程度で記述してください）</div>
                            </div>
                        )}
                    </div>
                ))}
            </section>

            <div className="page-break"></div>

            <section className="print-answers-section">
                <h2 className="print-section-title">解答・解説</h2>
                {questions.map((q, index) => (
                    <div key={q.id} className="print-answer-item">
                        <div className="print-a-header">
                            <strong>第 {index + 1} 問</strong>
                            <span className="print-a-correct">正解: {q.format === '多肢選択' ? q.choices.filter(c => c.is_correct).map(c => c.content).join('、') : q.correct_answer}</span>
                        </div>
                        {q.explanation && (
                            <div className="print-a-explanation">
                                <span className="print-label">【解説】</span>
                                <p>{q.explanation}</p>
                            </div>
                        )}
                    </div>
                ))}
            </section>
        </div>
    )
}
