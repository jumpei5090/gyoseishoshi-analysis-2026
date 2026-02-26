import { useState, useEffect } from 'react'
import { getTopicPredictions, getLawPredictions } from '../api/client'

const SUBJECT_COLORS = {
    '基礎法学': '#8b5cf6',
    '憲法': '#3b82f6',
    '行政法': '#10b981',
    '民法': '#f59e0b',
    '商法・会社法': '#ef4444',
}

const TREND_ICONS = { up: '📈', down: '📉', stable: '➡️', none: '—' }
const TREND_LABELS = { up: '上昇', down: '下降', stable: '横ばい', none: '—' }

function ScoreBar({ score, label, color }) {
    return (
        <div className="score-bar-row">
            <span className="score-bar-label">{label}</span>
            <div className="score-bar-track">
                <div
                    className="score-bar-fill"
                    style={{ width: `${score}%`, background: color || 'var(--accent)' }}
                />
            </div>
            <span className="score-bar-value">{score}%</span>
        </div>
    )
}

function MiniSparkline({ data }) {
    const max = Math.max(...data.map(d => d.count), 1)
    const w = 120
    const h = 28
    const points = data.map((d, i) => {
        const x = (i / (data.length - 1)) * w
        const y = h - (d.count / max) * (h - 4) - 2
        return `${x},${y}`
    }).join(' ')

    return (
        <svg width={w} height={h} className="sparkline-svg">
            <polyline
                points={points}
                fill="none"
                stroke="var(--accent)"
                strokeWidth="1.5"
                strokeLinejoin="round"
            />
            {data.map((d, i) => d.count > 0 && (
                <circle
                    key={i}
                    cx={(i / (data.length - 1)) * w}
                    cy={h - (d.count / max) * (h - 4) - 2}
                    r="2"
                    fill="var(--accent)"
                />
            ))}
        </svg>
    )
}

function TopicCard({ prediction, expanded, onToggle }) {
    const subjColor = SUBJECT_COLORS[prediction.subject_name] || 'var(--accent)'

    return (
        <div className={`prediction-card ${expanded ? 'expanded' : ''}`}>
            <div className="prediction-card-header" onClick={onToggle}>
                <div className="prediction-rank" style={{ background: subjColor }}>
                    {prediction.rank}
                </div>
                <div className="prediction-info">
                    <div className="prediction-title-row">
                        <span className="prediction-topic">{prediction.topic_name}</span>
                        <span className="prediction-trend-icon">{TREND_ICONS[prediction.trend_direction]}</span>
                    </div>
                    <div className="prediction-breadcrumb">
                        <span style={{ color: subjColor }}>{prediction.subject_name}</span>
                        <span className="prediction-sep">›</span>
                        <span>{prediction.law_name}</span>
                    </div>
                </div>
                <div className="prediction-score-badge">
                    <span className="prediction-score-value">{prediction.scores.composite}</span>
                    <span className="prediction-score-unit">点</span>
                </div>
            </div>

            {expanded && (
                <div className="prediction-detail">
                    <div className="prediction-stats-row">
                        <div className="prediction-stat">
                            <span className="stat-label">過去出題数</span>
                            <span className="stat-value">{prediction.total_appearances}問</span>
                        </div>
                        <div className="prediction-stat">
                            <span className="stat-label">出題年数</span>
                            <span className="stat-value">{prediction.years_appeared}/10年</span>
                        </div>
                        <div className="prediction-stat">
                            <span className="stat-label">最終出題</span>
                            <span className="stat-value">{prediction.last_year || '—'}年</span>
                        </div>
                        <div className="prediction-stat">
                            <span className="stat-label">トレンド</span>
                            <span className="stat-value">{TREND_LABELS[prediction.trend_direction]}</span>
                        </div>
                    </div>

                    <div className="prediction-sparkline-wrapper">
                        <span className="sparkline-label">出題推移（2015-2024）</span>
                        <MiniSparkline data={prediction.yearly_data} />
                    </div>

                    <div className="prediction-scores-detail">
                        <h4 className="scores-title">📊 分析スコア内訳</h4>
                        <ScoreBar score={prediction.scores.trend} label="トレンド" color="#3b82f6" />
                        <ScoreBar score={prediction.scores.cycle} label="周期性" color="#8b5cf6" />
                        <ScoreBar score={prediction.scores.recency} label="直近重要度" color="#10b981" />
                        <ScoreBar score={prediction.scores.gap} label="出題間隔" color="#f59e0b" />
                        <ScoreBar score={prediction.scores.bayesian} label="ベイズ確率" color="#ef4444" />
                        {prediction.scores.intervention_boost > 1.0 && (
                            <div className="intervention-boost-info">
                                <span className="boost-label">🚀 2026法改正インパクト:</span>
                                <span className="boost-value">×{prediction.scores.intervention_boost}</span>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}

function LawCard({ prediction, rank }) {
    const subjColor = SUBJECT_COLORS[prediction.subject_name] || 'var(--accent)'

    return (
        <div className="law-prediction-card">
            <div className="law-card-header">
                <div className="prediction-rank law-rank" style={{ background: subjColor }}>
                    {rank}
                </div>
                <div className="law-card-info">
                    <span className="law-card-name">{prediction.law_name}</span>
                    <span className="law-card-subject" style={{ color: subjColor }}>{prediction.subject_name}</span>
                </div>
                <div className="law-card-score">
                    <span className="law-score-value">{prediction.max_score}</span>
                    <span className="law-score-unit">点</span>
                </div>
            </div>
            <div className="law-card-body">
                <div className="law-card-meta">
                    <span>全{prediction.topic_count}テーマ</span>
                    <span>過去{prediction.total_questions}問出題</span>
                </div>
                <div className="law-top-topics">
                    {prediction.top_topics.map((t, i) => (
                        <div key={i} className="law-top-topic">
                            <span className="law-topic-rank">#{i + 1}</span>
                            <span className="law-topic-name">{t.name}</span>
                            <span className="law-topic-score">{t.score}点</span>
                            <span className="law-topic-trend">{TREND_ICONS[t.trend]}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default function PredictionPage() {
    const [topicPredictions, setTopicPredictions] = useState([])
    const [lawPredictions, setLawPredictions] = useState([])
    const [loading, setLoading] = useState(true)
    const [viewMode, setViewMode] = useState('topic') // 'topic' or 'law'
    const [expandedId, setExpandedId] = useState(null)
    const [filterSubject, setFilterSubject] = useState('all')

    useEffect(() => {
        Promise.all([getTopicPredictions(), getLawPredictions()])
            .then(([topics, laws]) => {
                setTopicPredictions(topics)
                setLawPredictions(laws)
            })
            .catch(err => console.error(err))
            .finally(() => setLoading(false))
    }, [])

    const subjects = [...new Set(topicPredictions.map(p => p.subject_name))]

    // Separate Legal and General Knowledge
    const legalSubjects = ['基礎法学', '憲法', '行政法', '民法', '商法・会社法']

    const legalTopics = topicPredictions.filter(p => legalSubjects.includes(p.subject_name))
    const knowledgeTopics = topicPredictions.filter(p => p.subject_name === '一般知識')

    const filteredLegal = filterSubject === 'all'
        ? legalTopics
        : legalTopics.filter(p => p.subject_name === filterSubject)

    const filteredKnowledge = filterSubject === 'all'
        ? knowledgeTopics
        : knowledgeTopics.filter(p => p.subject_name === filterSubject)

    const filteredLaws = filterSubject === 'all'
        ? lawPredictions
        : lawPredictions.filter(p => p.subject_name === filterSubject)

    // Helper to group by Law
    const groupByLaw = (topics) => {
        const groups = {}
        topics.forEach(t => {
            if (!groups[t.law_name]) groups[t.law_name] = []
            groups[t.law_name].push(t)
        })
        return groups
    }

    if (loading) {
        return (
            <div className="prediction-page">
                <div className="loading">
                    <div className="spinner" />
                    予測データを分析中...
                </div>
            </div>
        )
    }

    return (
        <div className="prediction-page">
            {/* Hero Header */}
            <div className="prediction-hero">
                <div className="prediction-hero-content">
                    <h1 className="prediction-hero-title">
                        🔮 2026年度 出題予測ランキング
                    </h1>
                    <p className="prediction-hero-subtitle">
                        過去10年間（2015〜2024）の出題データを回帰分析・周期性検出・ベイズ推定・
                        直近重要度分析・出題間隔分析、および「2026年法改正介入効果」の6手法で統計解析
                    </p>
                    <div className="prediction-hero-stats">
                        <div className="hero-stat">
                            <span className="hero-stat-value">{topicPredictions.length}</span>
                            <span className="hero-stat-label">分析テーマ</span>
                        </div>
                        <div className="hero-stat">
                            <span className="hero-stat-value">600</span>
                            <span className="hero-stat-label">過去問分析数</span>
                        </div>
                        <div className="hero-stat">
                            <span className="hero-stat-value">10</span>
                            <span className="hero-stat-label">年間データ</span>
                        </div>
                        <div className="hero-stat">
                            <span className="hero-stat-value">6</span>
                            <span className="hero-stat-label">統計手法</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Controls */}
            <div className="prediction-controls">
                <div className="prediction-view-toggle">
                    <button
                        className={`toggle-btn ${viewMode === 'topic' ? 'active' : ''}`}
                        onClick={() => setViewMode('topic')}
                    >
                        🏷️ テーマ別
                    </button>
                    <button
                        className={`toggle-btn ${viewMode === 'law' ? 'active' : ''}`}
                        onClick={() => setViewMode('law')}
                    >
                        📚 法律/章別
                    </button>
                </div>
                <div className="prediction-filter">
                    <select
                        value={filterSubject}
                        onChange={e => setFilterSubject(e.target.value)}
                        className="filter-select"
                    >
                        <option value="all">全科目</option>
                        {subjects.map(s => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </select>
                </div>
            </div>

            {/* Rankings */}
            <div className="prediction-rankings">
                {viewMode === 'topic' ? (
                    <>
                        {/* Section 1: Legal Subjects */}
                        {(filterSubject === 'all' || legalSubjects.includes(filterSubject)) && (
                            <div className="prediction-section">
                                <h2 className="section-title main-section-title">⚖️ 法令等科目（メイン）</h2>
                                <div className="topic-rankings">
                                    {Object.entries(groupByLaw(filteredLegal)).map(([lawName, topics]) => (
                                        <div key={lawName} className="law-group">
                                            <h3 className="law-group-title">{lawName}</h3>
                                            {topics.map(p => (
                                                <TopicCard
                                                    key={p.topic_id}
                                                    prediction={p}
                                                    expanded={expandedId === p.topic_id}
                                                    onToggle={() => setExpandedId(expandedId === p.topic_id ? null : p.topic_id)}
                                                />
                                            ))}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Section 2: General Knowledge */}
                        {(filterSubject === 'all' || filterSubject === '一般知識') && (
                            <div className="prediction-section sub-section">
                                <h2 className="section-title sub-section-title">📝 基礎知識・行政書士法（別枠）</h2>
                                <div className="topic-rankings">
                                    {filteredKnowledge.map(p => (
                                        <TopicCard
                                            key={p.topic_id}
                                            prediction={p}
                                            expanded={expandedId === p.topic_id}
                                            onToggle={() => setExpandedId(expandedId === p.topic_id ? null : p.topic_id)}
                                        />
                                    ))}
                                </div>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="law-rankings">
                        {filteredLaws.map((p, i) => (
                            <LawCard key={p.law_id} prediction={p} rank={i + 1} />
                        ))}
                    </div>
                )}
            </div>

            {/* Method explanation */}
            <div className="prediction-methods card">
                {/* ... (keep existing explanation but maybe simpler) ... */}
                <div className="card-header">
                    <span className="card-title">📐 使用統計手法</span>
                </div>
                <div className="methods-grid">
                    <div className="method-item">
                        <div className="method-icon" style={{ background: '#3b82f6' }}>📈</div>
                        <div className="method-info">
                            <h4>線形回帰分析</h4>
                            <p>10年間の時系列データに回帰直線をフィットし、2026年の出題数をトレンド外挿で予測</p>
                        </div>
                    </div>
                    <div className="method-item">
                        <div className="method-icon" style={{ background: '#8b5cf6' }}>🔄</div>
                        <div className="method-info">
                            <h4>周期性検出</h4>
                            <p>出題間隔の平均・分散を算出し、2026年が周期パターンに合致するかを評価</p>
                        </div>
                    </div>
                    <div className="method-item">
                        <div className="method-icon" style={{ background: '#10b981' }}>⏱️</div>
                        <div className="method-info">
                            <h4>指数減衰重み付け</h4>
                            <p>直近の出題を重視する演算（λ=0.3）で重み付けした出題頻度を算出</p>
                        </div>
                    </div>
                    <div className="method-item">
                        <div className="method-icon" style={{ background: '#f59e0b' }}>📊</div>
                        <div className="method-info">
                            <h4>出題間隔分析</h4>
                            <p>最終出題からの年数を分析し、「出題されるべき時期」に来ているテーマを特定</p>
                        </div>
                    </div>
                    <div className="method-item">
                        <div className="method-icon" style={{ background: '#ef4444' }}>🎯</div>
                        <div className="method-info">
                            <h4>ベイズ推定（減衰更新）</h4>
                            <p>Beta-Binomialモデルに指数減衰（γ=0.85）を導入。過去の記憶を段階的に忘却</p>
                        </div>
                    </div>
                    <div className="method-item">
                        <div className="method-icon" style={{ background: '#f59e0b', color: '#fff' }}>🚀</div>
                        <div className="method-info">
                            <h4>2026法改正介入効果</h4>
                            <p>2026年1月施行の行政書士法改正を「構造的切断」として考慮し確率をブースト</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Disclaimer */}
            <div className="prediction-disclaimer">
                <p>
                    ⚠️ 本予測は過去10年間の出題データに基づく統計的分析です。
                    実際の試験は試験委員の判断により出題されるため、
                    予測と異なる場合があります。学習計画の参考としてご活用ください。
                </p>
            </div>
        </div>
    )
}
