import { useState, useEffect, useRef } from 'react'
import { getSingleQuestion } from '../api/client'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const SUBJECT_COLORS = {
    '基礎法学': '#58a6ff',
    '憲法': '#3fb950',
    '行政法': '#d29922',
    '民法': '#a371f7',
    '商法・会社法': '#f85149',
    '一般知識': '#f778ba',
}

const YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]

/* ─── Subject Trend Chart (Bar + Line) ─── */
function SubjectTrendChart({ subject }) {
    const canvasRef = useRef(null)
    const chartRef = useRef(null)

    useEffect(() => {
        if (!subject || !subject.topics) return

        // Aggregate yearly counts across all topics for this subject
        const yearlyTotals = {}
        YEARS.forEach(y => { yearlyTotals[y] = 0 })
        subject.topics.forEach(topic => {
            topic.yearly.forEach(yd => {
                yearlyTotals[yd.year] = (yearlyTotals[yd.year] || 0) + yd.count
            })
        })

        const counts = YEARS.map(y => yearlyTotals[y] || 0)
        const color = SUBJECT_COLORS[subject.subject_name] || '#8b949e'

        if (chartRef.current) chartRef.current.destroy()

        const ctx = canvasRef.current.getContext('2d')
        const gradient = ctx.createLinearGradient(0, 0, 0, 200)
        gradient.addColorStop(0, color + '4D') // 30% opacity
        gradient.addColorStop(1, color + '05') // ~2% opacity

        chartRef.current = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: YEARS.map(y => `${y}年`),
                datasets: [
                    {
                        label: `${subject.subject_name} 出題数`,
                        data: counts,
                        backgroundColor: gradient,
                        borderColor: color + 'CC',
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false,
                    },
                    {
                        label: 'トレンド',
                        data: counts,
                        type: 'line',
                        borderColor: color,
                        backgroundColor: 'transparent',
                        borderWidth: 2.5,
                        pointBackgroundColor: color,
                        pointBorderColor: '#0d1117',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        tension: 0.3,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            color: '#8b949e',
                            font: { family: 'Noto Sans JP', size: 11 },
                            usePointStyle: true,
                            padding: 16,
                        },
                    },
                    tooltip: {
                        backgroundColor: '#1c2128',
                        titleColor: '#e6edf3',
                        bodyColor: '#8b949e',
                        borderColor: '#30363d',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 10,
                        titleFont: { family: 'Noto Sans JP', size: 12 },
                        bodyFont: { family: 'Noto Sans JP', size: 12 },
                        callbacks: {
                            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y} 問`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(48, 54, 61, 0.4)', drawBorder: false },
                        ticks: { color: '#8b949e', font: { family: 'Noto Sans JP', size: 11 } },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(48, 54, 61, 0.4)', drawBorder: false },
                        ticks: {
                            color: '#8b949e',
                            font: { family: 'Noto Sans JP', size: 11 },
                            stepSize: 1,
                            callback: (v) => Number.isInteger(v) ? v : '',
                        },
                    },
                },
            },
        })

        return () => {
            if (chartRef.current) chartRef.current.destroy()
        }
    }, [subject])

    return (
        <div className="subject-trend-chart">
            <canvas ref={canvasRef}></canvas>
        </div>
    )
}

/* ─── Topic Trend Chart (Bar + Line) ─── */
function TopicTrendChart({ topic, color }) {
    const canvasRef = useRef(null)
    const chartRef = useRef(null)

    useEffect(() => {
        if (!topic || !topic.yearly) return

        const yearlyTotals = {}
        YEARS.forEach(y => { yearlyTotals[y] = 0 })
        topic.yearly.forEach(yd => {
            yearlyTotals[yd.year] = yd.count
        })

        const counts = YEARS.map(y => yearlyTotals[y] || 0)

        if (chartRef.current) chartRef.current.destroy()

        const ctx = canvasRef.current.getContext('2d')
        const gradient = ctx.createLinearGradient(0, 0, 0, 150)
        gradient.addColorStop(0, color + '33') // 20% opacity
        gradient.addColorStop(1, color + '00') // 0% opacity

        chartRef.current = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: YEARS.map(y => `${y}年`),
                datasets: [
                    {
                        label: `${topic.topic_name} 出題数`,
                        data: counts,
                        backgroundColor: gradient,
                        borderColor: color + '99',
                        borderWidth: 1.5,
                        borderRadius: 4,
                    },
                    {
                        label: 'トレンド',
                        data: counts,
                        type: 'line',
                        borderColor: color,
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointBackgroundColor: color,
                        pointRadius: 3,
                        tension: 0.3,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1c2128',
                        callbacks: {
                            label: (ctx) => `${ctx.parsed.y} 問`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#8b949e', font: { size: 10 } },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(48, 54, 61, 0.2)' },
                        ticks: {
                            color: '#8b949e',
                            font: { size: 10 },
                            stepSize: 1,
                            callback: (v) => Number.isInteger(v) ? v : '',
                        },
                    },
                },
            },
        })

        return () => {
            if (chartRef.current) chartRef.current.destroy()
        }
    }, [topic, color])

    return (
        <div className="topic-trend-chart">
            <canvas ref={canvasRef}></canvas>
        </div>
    )
}


/* ─── Single Question Modal ─── */
function SingleQuestionModal({ year, questionNumber, onClose }) {
    const [question, setQuestion] = useState(null)
    const [loading, setLoading] = useState(true)
    const [showAnswer, setShowAnswer] = useState(false)

    useEffect(() => {
        setLoading(true)
        setShowAnswer(false)
        getSingleQuestion(year, questionNumber)
            .then(data => setQuestion(data))
            .catch(err => console.error(err))
            .finally(() => setLoading(false))
    }, [year, questionNumber])

    useEffect(() => {
        const handleKey = (e) => { if (e.key === 'Escape') onClose() }
        window.addEventListener('keydown', handleKey)
        return () => window.removeEventListener('keydown', handleKey)
    }, [onClose])

    const isKijutsu = question?.format === '記述' || question?.format === '記述式'
    const isTashisentaku = question?.format === '多肢選択' || question?.format === '多肢選択式'

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content question-viewer-modal" onClick={e => e.stopPropagation()}>
                {/* Header */}
                <div className="modal-header">
                    <div>
                        <h2 className="modal-title">
                            📝 {year}年度 問{questionNumber}
                        </h2>
                        {question && (
                            <p className="modal-subtitle">
                                {question.subject_name}
                                {question.law_name && ` › ${question.law_name}`}
                                {question.format && ` ── ${question.format}`}
                            </p>
                        )}
                    </div>
                    <button className="modal-close" onClick={onClose}>✕</button>
                </div>

                {/* Body */}
                <div className="modal-body">
                    {loading ? (
                        <div className="loading">
                            <div className="spinner" />
                            問題を読み込み中...
                        </div>
                    ) : !question ? (
                        <div className="empty-state" style={{ padding: '32px 0' }}>
                            <div className="empty-icon">📭</div>
                            <h3>問題が見つかりませんでした</h3>
                        </div>
                    ) : (
                        <div className="question-viewer-body">
                            {/* Question Text */}
                            <div className="qv-question-text">
                                {question.question_text || `（${year}年度 問${questionNumber}）問題文はまだ登録されていません。`}
                            </div>

                            {/* Choices */}
                            {question.choices && question.choices.length > 0 && (
                                <div className="qv-choices">
                                    {isKijutsu ? (
                                        <div className="qv-kijutsu-notice">
                                            ※ 記述式問題です。解答欄に記述してください。
                                        </div>
                                    ) : isTashisentaku ? (
                                        <div className="qv-tashisentaku">
                                            <div className="qv-choices-label">【語群】</div>
                                            <div className="qv-tashisentaku-grid">
                                                {question.choices.map((c, i) => (
                                                    <div
                                                        key={i}
                                                        className={`qv-choice-item tashisentaku ${showAnswer && c.is_correct ? 'correct' : ''}`}
                                                    >
                                                        <span className="qv-choice-content">{c.content}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ) : (
                                        question.choices.map((c, i) => (
                                            <div
                                                key={i}
                                                className={`qv-choice-item ${showAnswer ? (c.is_correct ? 'correct' : 'wrong') : ''}`}
                                            >
                                                <span className="qv-choice-number">{c.choice_number}</span>
                                                <span className="qv-choice-content">{c.content}</span>
                                                {showAnswer && c.is_correct && (
                                                    <span className="qv-correct-badge">✓ 正解</span>
                                                )}
                                            </div>
                                        ))
                                    )}
                                </div>
                            )}

                            {/* Answer Button */}
                            {!showAnswer ? (
                                <button
                                    className="qv-answer-btn"
                                    onClick={() => setShowAnswer(true)}
                                >
                                    🔓 回答を見る
                                </button>
                            ) : (
                                <div className="qv-answer-section">
                                    <div className="qv-answer-header">
                                        <span className="qv-answer-badge">✅ 正解</span>
                                        <span className="qv-answer-value">{question.correct_answer}</span>
                                    </div>
                                    {question.explanation && (
                                        <div className="qv-explanation">
                                            <div className="qv-explanation-label">📖 解説</div>
                                            <div className="qv-explanation-text">{question.explanation}</div>
                                        </div>
                                    )}
                                    <button
                                        className="qv-hide-btn"
                                        onClick={() => setShowAnswer(false)}
                                    >
                                        🔒 回答を隠す
                                    </button>
                                </div>
                            )}

                            {/* Topic Tags */}
                            {question.topics && question.topics.length > 0 && (
                                <div className="qv-topics">
                                    {question.topics.map((t, i) => (
                                        <span key={i} className="qv-topic-tag">{t}</span>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

/* ─── Main Component ─── */
export default function TopicBreakdownTable({ data }) {
    const [expandedSubjects, setExpandedSubjects] = useState({})
    const [expandedTopics, setExpandedTopics] = useState({})
    const [selectedQuestion, setSelectedQuestion] = useState(null) // {year, questionNumber}

    const toggleSubject = (id) => {
        setExpandedSubjects(prev => ({ ...prev, [id]: !prev[id] }))
    }

    const toggleTopic = (key) => {
        setExpandedTopics(prev => ({ ...prev, [key]: !prev[key] }))
    }

    const openQuestion = (year, questionNumber, e) => {
        e.stopPropagation()
        setSelectedQuestion({ year, questionNumber })
    }

    if (!data || data.length === 0) {
        return <div className="loading">データ読み込み中...</div>
    }

    return (
        <div className="topic-breakdown">
            {data.map(subject => {
                const color = SUBJECT_COLORS[subject.subject_name] || '#8b949e'
                const isExpanded = expandedSubjects[subject.subject_id]

                return (
                    <div key={subject.subject_id} className="topic-subject-group">
                        {/* Subject Header */}
                        <div
                            className="topic-subject-header"
                            onClick={() => toggleSubject(subject.subject_id)}
                            style={{ borderLeftColor: color }}
                        >
                            <div className="topic-subject-info">
                                <span className="topic-expand-icon">{isExpanded ? '▼' : '▶'}</span>
                                <span className="topic-subject-name" style={{ color }}>
                                    {subject.subject_name}
                                </span>
                                <span className="topic-subject-count">
                                    {subject.topics.length}テーマ
                                </span>
                            </div>
                            <span className="topic-subject-total" style={{ color }}>
                                {subject.subject_total}問
                            </span>
                        </div>

                        {/* Topics Table */}
                        {isExpanded && (
                            <div className="topic-table-wrapper">
                                <SubjectTrendChart subject={subject} />
                                <table className="topic-detail-table">
                                    <thead>
                                        <tr>
                                            <th className="th-topic">テーマ</th>
                                            {YEARS.map(y => (
                                                <th key={y} className="th-year">{String(y).slice(2)}</th>
                                            ))}
                                            <th className="th-total">計</th>
                                            <th className="th-prediction">2026予測</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {subject.topics.map(topic => {
                                            const topicKey = `${subject.subject_id}-${topic.topic_id}`
                                            const isTopicExpanded = expandedTopics[topicKey]

                                            return (
                                                <>
                                                    <tr
                                                        key={topicKey}
                                                        className={`topic-row ${isTopicExpanded ? 'expanded' : ''}`}
                                                        onClick={() => toggleTopic(topicKey)}
                                                    >
                                                        <td className="td-topic">
                                                            <span className="topic-expand-mini">
                                                                {isTopicExpanded ? '▾' : '▸'}
                                                            </span>
                                                            {topic.topic_name}
                                                        </td>
                                                        {topic.yearly.map(yd => (
                                                            <td
                                                                key={yd.year}
                                                                className={`td-count ${yd.count === 0 ? 'zero' : yd.count >= 3 ? 'high' : ''}`}
                                                            >
                                                                {yd.count > 0 ? yd.count : '−'}
                                                            </td>
                                                        ))}
                                                        <td className="td-total">{topic.total}</td>
                                                        <td className="td-prediction">
                                                            {topic.prediction ? (
                                                                <div className="pred-score-container" title={`2026予測ランク: ${topic.prediction.rank}位`}>
                                                                    <div className="pred-score-text" style={{
                                                                        color: topic.prediction.score >= 80 ? '#f59e0b' : topic.prediction.score >= 60 ? '#10b981' : '#8b949e',
                                                                        fontWeight: 'bold',
                                                                        fontSize: '0.8rem'
                                                                    }}>
                                                                        {topic.prediction.score}%
                                                                    </div>
                                                                    <div className="pred-score-bar-bg">
                                                                        <div
                                                                            className={`pred-score-bar-fill ${topic.prediction.score >= 80 ? 'high' : topic.prediction.score >= 60 ? 'mid' : 'low'}`}
                                                                            style={{ width: `${topic.prediction.score}%` }}
                                                                        />
                                                                    </div>
                                                                </div>
                                                            ) : '−'}
                                                        </td>
                                                    </tr>
                                                    {isTopicExpanded && (
                                                        <tr key={`${topicKey}-detail`} className="topic-detail-row">
                                                            <td colSpan={YEARS.length + 3}>
                                                                <div className="topic-year-details">
                                                                    {/* Sub-theme Trend Chart */}
                                                                    <TopicTrendChart topic={topic} color={color} />

                                                                    <div className="year-question-group-header" style={{ marginBottom: '0.5rem', color: '#8b949e', fontSize: '0.8rem' }}>
                                                                        📌 出題問題の特定（クリックで詳細表示）
                                                                    </div>

                                                                    <div className="year-question-list">
                                                                        {topic.yearly
                                                                            .filter(yd => yd.count > 0)
                                                                            .map(yd => (
                                                                                <div key={yd.year} className="year-question-group">
                                                                                    <div className="year-label">{yd.year}年</div>
                                                                                    <div className="year-questions">
                                                                                        {yd.questions.map(q => (
                                                                                            <span
                                                                                                key={q.id}
                                                                                                className="question-chip clickable"
                                                                                                onClick={(e) => openQuestion(yd.year, q.question_number, e)}
                                                                                                title={`${yd.year}年 問${q.question_number} をクリックして問題を表示`}
                                                                                            >
                                                                                                問{q.question_number}
                                                                                                {q.format && <span className="q-format">({q.format})</span>}
                                                                                            </span>
                                                                                        ))}
                                                                                    </div>
                                                                                </div>
                                                                            ))}
                                                                    </div>
                                                                </div>
                                                            </td>
                                                        </tr>
                                                    )}
                                                </>
                                            )
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                )
            })}

            {/* Question Viewer Modal */}
            {selectedQuestion && (
                <SingleQuestionModal
                    year={selectedQuestion.year}
                    questionNumber={selectedQuestion.questionNumber}
                    onClose={() => setSelectedQuestion(null)}
                />
            )}
        </div>
    )
}
