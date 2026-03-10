import { useState, useEffect } from 'react'
import { getTaxonomy, getQuestionsByTopic, getHistory } from '../api/client'
import PracticeMode from './PracticeMode'
import MockExamMode from './MockExamMode'
import PrintableQuestionSheet from './PrintableQuestionSheet'

function TopicCount({ count }) {
    if (count == null) return null
    return <span className="topic-count">{count}問</span>
}

function HistoryBadge({ record }) {
    if (!record) return <span className="history-badge untried">未実施</span>
    const date = new Date(record.answered_at)
    const label = `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    if (record.is_correct) {
        return <span className="history-badge pass">✅ {label}</span>
    }
    return <span className="history-badge fail">❌ {label}</span>
}

export default function QuestionBrowserPage({ nickname, initialTopicId, onTopicConsumed }) {
    const [taxonomy, setTaxonomy] = useState([])
    const [selectedSubject, setSelectedSubject] = useState(null)
    const [selectedLaw, setSelectedLaw] = useState(null)
    const [selectedTopic, setSelectedTopic] = useState(null)
    const [questions, setQuestions] = useState([])
    const [loadingQ, setLoadingQ] = useState(false)
    const [mode, setMode] = useState(null) // null | 'practice' | 'mock'
    const [topicCounts, setTopicCounts] = useState({}) // topic_id → count
    const [history, setHistory] = useState({}) // question_id → {is_correct, answered_at}

    // Load taxonomy once
    useEffect(() => {
        getTaxonomy().then(data => {
            setTaxonomy(data)
            if (data.length > 0) setSelectedSubject(data[0])
        }).catch(console.error)
    }, [])

    // Auto-select topic when navigated from search
    useEffect(() => {
        if (!initialTopicId || taxonomy.length === 0) return
        // Walk the taxonomy to find subject/law containing this topic
        for (const subject of taxonomy) {
            for (const law of subject.laws) {
                const found = law.topics.find(t => t.id === initialTopicId)
                if (found) {
                    setSelectedSubject(subject)
                    // Need to set law after subject renders, use small delay
                    setTimeout(() => {
                        setSelectedLaw(law)
                        setTimeout(() => {
                            setSelectedTopic(found)
                            if (onTopicConsumed) onTopicConsumed()
                        }, 50)
                    }, 50)
                    return
                }
            }
        }
    }, [initialTopicId, taxonomy])

    // Load history when nickname changes or mode exits (refreshes after answering)
    const loadHistory = () => {
        if (!nickname) return
        getHistory(nickname).then(setHistory).catch(console.error)
    }
    useEffect(loadHistory, [nickname])

    // When a topic is selected, fetch questions
    useEffect(() => {
        if (!selectedTopic) { setQuestions([]); return }
        setLoadingQ(true)
        getQuestionsByTopic(selectedTopic.id)
            .then(data => {
                setQuestions(data)
                setTopicCounts(prev => ({ ...prev, [selectedTopic.id]: data.length }))
            })
            .catch(console.error)
            .finally(() => setLoadingQ(false))
    }, [selectedTopic])

    // Select first law when subject changes
    useEffect(() => {
        setSelectedTopic(null)
        setMode(null)
        if (selectedSubject && selectedSubject.laws.length > 0) {
            setSelectedLaw(selectedSubject.laws[0])
        } else {
            setSelectedLaw(null)
        }
    }, [selectedSubject])

    // Deselect topic when law changes
    useEffect(() => {
        setSelectedTopic(null)
        setMode(null)
    }, [selectedLaw])

    const handleModeFinish = () => {
        setMode(null)
        loadHistory() // refresh badges after answering
    }

    if (mode === 'practice') {
        return (
            <div className="browser-page">
                <PracticeMode questions={questions} onFinish={handleModeFinish} nickname={nickname} />
            </div>
        )
    }

    if (mode === 'mock') {
        return (
            <div className="browser-page">
                <MockExamMode questions={questions} onFinish={handleModeFinish} nickname={nickname} />
            </div>
        )
    }

    const laws = selectedSubject ? selectedSubject.laws : []
    const topics = selectedLaw ? selectedLaw.topics : []

    // Progress stats for selected topic
    const topicQuestions = questions
    const attempted = topicQuestions.filter(q => history[q.id])
    const correct = attempted.filter(q => history[q.id]?.is_correct)

    return (
        <div className="browser-page">
            <div className="browser-layout">
                {/* ─── Left Panel: Navigation ─── */}
                <aside className="browser-sidebar">
                    {/* Subject tabs */}
                    <div className="browser-section-title">分野</div>
                    <div className="subject-tabs">
                        {taxonomy.map(s => (
                            <button
                                key={s.id}
                                className={`subject-tab ${selectedSubject?.id === s.id ? 'active' : ''}`}
                                onClick={() => setSelectedSubject(s)}
                            >
                                {s.name}
                            </button>
                        ))}
                    </div>

                    {/* Law list */}
                    {laws.length > 0 && (
                        <>
                            <div className="browser-section-title">法律 / 章</div>
                            <div className="law-list">
                                {laws.map(l => (
                                    <button
                                        key={l.id}
                                        className={`law-item ${selectedLaw?.id === l.id ? 'active' : ''}`}
                                        onClick={() => setSelectedLaw(l)}
                                    >
                                        <span>{l.name}</span>
                                        <span className="law-topic-count">{l.topics.length}テーマ</span>
                                    </button>
                                ))}
                            </div>
                        </>
                    )}

                    {/* Topic list */}
                    {topics.length > 0 && (
                        <>
                            <div className="browser-section-title">テーマ</div>
                            <div className="topic-list">
                                {topics.map(t => (
                                    <button
                                        key={t.id}
                                        className={`topic-item ${selectedTopic?.id === t.id ? 'active' : ''}`}
                                        onClick={() => setSelectedTopic(t)}
                                    >
                                        <span>{t.name}</span>
                                        <TopicCount count={topicCounts[t.id]} />
                                    </button>
                                ))}
                            </div>
                        </>
                    )}
                </aside>

                {/* ─── Right Panel: Content ─── */}
                <main className="browser-main">
                    {!selectedTopic ? (
                        <div className="browser-placeholder">
                            <div className="placeholder-icon">📚</div>
                            <h2>トピックを選択してください</h2>
                            <p>左のメニューから <strong>分野 → 法律 → テーマ</strong> の順に選択すると、過去11年分の問題が表示されます</p>
                        </div>
                    ) : loadingQ ? (
                        <div className="browser-loading">
                            <div className="spinner" />
                            <p>問題を読み込み中...</p>
                        </div>
                    ) : (
                        <div className="browser-content">
                            {/* Topic Header */}
                            <div className="browser-topic-header">
                                <div className="breadcrumb">
                                    <span>{selectedSubject?.name}</span>
                                    <span className="breadcrumb-sep">›</span>
                                    <span>{selectedLaw?.name}</span>
                                    <span className="breadcrumb-sep">›</span>
                                    <strong>{selectedTopic?.name}</strong>
                                </div>
                                <div className="question-count-badge">
                                    {questions.length}問（2015〜2025年）
                                </div>
                                <button className="btn btn-outline print-btn" onClick={() => window.print()}>
                                    <span>🖨️ 印刷する (A4)</span>
                                </button>
                            </div>

                            {/* My Progress (if any history) */}
                            {nickname && attempted.length > 0 && (
                                <div className="topic-progress-bar">
                                    <div className="topic-progress-label">
                                        <span>📊 自分の進捗</span>
                                        <span className="topic-progress-stats">
                                            {attempted.length}/{questions.length}問実施　✅ {correct.length}問正解
                                        </span>
                                    </div>
                                    <div className="topic-progress-track">
                                        <div
                                            className="topic-progress-fill attempted"
                                            style={{ width: `${(attempted.length / questions.length) * 100}%` }}
                                        />
                                        <div
                                            className="topic-progress-fill correct-fill"
                                            style={{ width: `${(correct.length / questions.length) * 100}%` }}
                                        />
                                    </div>
                                </div>
                            )}

                            {questions.length === 0 ? (
                                <div className="browser-empty">
                                    <div className="empty-icon">📭</div>
                                    <p>このトピックには現在問題データがありません</p>
                                </div>
                            ) : (
                                <>
                                    {/* Year distribution summary */}
                                    <div className="year-summary">
                                        {Array.from(new Set(questions.map(q => q.year))).sort().map(year => {
                                            const cnt = questions.filter(q => q.year === year).length
                                            return (
                                                <div key={year} className="year-chip">
                                                    <span className="year-chip-year">{year}年</span>
                                                    <span className="year-chip-count">{cnt}問</span>
                                                </div>
                                            )
                                        })}
                                    </div>

                                    {/* Mode Selection */}
                                    <div className="mode-select-area">
                                        <div className="mode-select-label">演習モードを選択</div>
                                        <div className="mode-buttons">
                                            <button className="mode-btn practice" onClick={() => setMode('practice')}>
                                                <span className="mode-btn-icon">📖</span>
                                                <span className="mode-btn-title">練習モード</span>
                                                <span className="mode-btn-desc">1問ずつ即時正誤確認 + 解説</span>
                                            </button>
                                            <button className="mode-btn mock" onClick={() => setMode('mock')}>
                                                <span className="mode-btn-icon">📝</span>
                                                <span className="mode-btn-title">本番練習用モード</span>
                                                <span className="mode-btn-desc">全問回答後に正答率 + 解説確認</span>
                                            </button>
                                        </div>
                                    </div>

                                    {/* Question Preview List with history badges */}
                                    <div className="browser-question-preview">
                                        <div className="preview-title">📋 問題一覧</div>
                                        <div className="preview-list">
                                            {questions.map((q, i) => (
                                                <div key={q.id} className={`preview-item ${history[q.id] ? (history[q.id].is_correct ? 'done-pass' : 'done-fail') : ''}`}>
                                                    <span className="preview-num">#{i + 1}</span>
                                                    <span className="preview-year">{q.year}年度</span>
                                                    <span className="preview-qnum">問{q.question_number}</span>
                                                    <span className="preview-format">{q.format}</span>
                                                    <span className="preview-text">{q.question_text?.slice(0, 40)}...</span>
                                                    <HistoryBadge record={history[q.id]} />
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                </main>
            </div>
            <PrintableQuestionSheet
                questions={questions}
                subjectName={selectedSubject?.name}
                lawName={selectedLaw?.name}
                topicName={selectedTopic?.name}
            />
        </div>
    )
}
