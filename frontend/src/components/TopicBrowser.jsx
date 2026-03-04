import { useState, useEffect } from 'react'
import { getTaxonomy, searchFrequency } from '../api/client'

export default function TopicBrowser({ onSearch, onLoadingChange, onNavigateToTopic }) {
    const [taxonomy, setTaxonomy] = useState([])
    const [activeSubject, setActiveSubject] = useState(null)
    const [activeLaw, setActiveLaw] = useState(null)

    useEffect(() => {
        getTaxonomy()
            .then(data => {
                setTaxonomy(data)
                if (data.length > 0) setActiveSubject(data[0].id)
            })
            .catch(err => console.error('分類データ読み込み失敗:', err))
    }, [])

    const currentSubject = taxonomy.find(s => s.id === activeSubject)

    const handleTopicClick = async (name) => {
        onLoadingChange(true)
        try {
            const result = await searchFrequency(name)
            onSearch(result)
        } catch (err) {
            console.error(err)
        } finally {
            onLoadingChange(false)
        }
    }

    const handleLawClick = async (name) => {
        onLoadingChange(true)
        try {
            const result = await searchFrequency(name)
            onSearch(result)
        } catch (err) {
            console.error(err)
        } finally {
            onLoadingChange(false)
        }
    }

    if (taxonomy.length === 0) return null

    return (
        <div className="topic-browser">
            <div className="card">
                <div className="card-header">
                    <span className="card-title">📂 分野から選んで分析</span>
                    <span className="card-subtitle">分野 → 法律 → テーマを選択</span>
                </div>

                {/* Subject Tabs */}
                <div className="subject-tabs">
                    {taxonomy.map(s => (
                        <button
                            key={s.id}
                            className={`subject-tab ${activeSubject === s.id ? 'active' : ''}`}
                            onClick={() => { setActiveSubject(s.id); setActiveLaw(null) }}
                        >
                            {s.name}
                        </button>
                    ))}
                </div>

                {/* Laws & Topics Panel */}
                {currentSubject && (
                    <div className="taxonomy-panel">
                        {currentSubject.laws.map(law => (
                            <div key={law.id} className="law-section">
                                <div
                                    className={`law-header ${activeLaw === law.id ? 'active' : ''}`}
                                    onClick={() => setActiveLaw(activeLaw === law.id ? null : law.id)}
                                >
                                    <span className="law-name">
                                        <span className="law-chevron">{activeLaw === law.id ? '▼' : '▶'}</span>
                                        {law.name}
                                    </span>
                                    <button
                                        className="law-search-btn"
                                        onClick={(e) => { e.stopPropagation(); handleLawClick(law.name) }}
                                        title={`${law.name}の出題傾向を表示`}
                                    >
                                        📊 分析
                                    </button>
                                </div>

                                {activeLaw === law.id && (
                                    <div className="topic-chips">
                                        {law.topics.map(topic => (
                                            <div key={topic.id} className="topic-chip-group">
                                                <span
                                                    className="topic-chip"
                                                    onClick={() => handleTopicClick(topic.name)}
                                                    title={`出題傾向グラフで分析${topic.prediction ? ` (2026重要度: ${topic.prediction.score}%)` : ''}`}>
                                                    {topic.name}
                                                    {topic.prediction && (
                                                        <span className={`topic-pred-mini ${topic.prediction.score >= 80 ? 'high' : topic.prediction.score >= 60 ? 'mid' : 'low'}`}>
                                                            {topic.prediction.score}%
                                                        </span>
                                                    )}
                                                </span>
                                                {onNavigateToTopic && (
                                                    <button
                                                        className="topic-chip-goto"
                                                        onClick={() => onNavigateToTopic(topic.id)}
                                                        title="過去問ブラウザで開く"
                                                    >
                                                        📚
                                                    </button>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
