import { useState, useEffect } from 'react'
import { getSubjectBreakdown, getSubjects, getTopicBreakdown } from '../api/client'
import FrequencyChart from './FrequencyChart'
import FrequencyTable from './FrequencyTable'
import SubjectBreakdown from './SubjectBreakdown'
import TopicBreakdownTable from './TopicBreakdownTable'

export default function Dashboard({ searchResult, loading }) {
    const [subjectData, setSubjectData] = useState([])
    const [subjects, setSubjects] = useState([])
    const [topicData, setTopicData] = useState([])

    useEffect(() => {
        loadInitialData()
    }, [])

    const loadInitialData = async () => {
        try {
            const [breakdown, subjs, topics] = await Promise.all([
                getSubjectBreakdown(),
                getSubjects(),
                getTopicBreakdown(),
            ])
            setSubjectData(breakdown)
            setSubjects(subjs)
            setTopicData(topics)
        } catch (err) {
            console.error('初期データの読み込みに失敗:', err)
        }
    }

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner" />
                検索中...
            </div>
        )
    }

    // Show search results
    if (searchResult) {
        const { keyword, matched_topics, yearly_data, total_count } = searchResult
        const years = yearly_data.filter(y => y.count > 0).length
        const maxYear = yearly_data.reduce((max, y) => y.count > max.count ? y : max, { count: 0 })
        const avgCount = years > 0 ? (total_count / yearly_data.length).toFixed(1) : 0

        return (
            <div>
                {/* Stats */}
                <div className="stats-grid">
                    <div className="stat-card">
                        <div className="stat-value">{total_count}</div>
                        <div className="stat-label">総出題数</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{years}</div>
                        <div className="stat-label">出題年数 / {yearly_data.length}年</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{avgCount}</div>
                        <div className="stat-label">年平均出題数</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-value">{maxYear.year || '-'}</div>
                        <div className="stat-label">最多出題年 ({maxYear.count}問)</div>
                    </div>
                </div>

                {/* Matched Topics */}
                {matched_topics.length > 0 && (
                    <div className="matched-topics">
                        {matched_topics.map((t, i) => (
                            <span key={i} className="topic-tag">
                                {t.subject_name && `${t.subject_name} › `}{t.law_name && t.law_name !== t.name ? `${t.law_name} › ` : ''}{t.name}
                            </span>
                        ))}
                    </div>
                )}

                {/* Charts */}
                <div className="dashboard-grid">
                    <div className="card full-width">
                        <div className="card-header">
                            <span className="card-title">📊 「{keyword}」年度別出題頻度</span>
                        </div>
                        <FrequencyChart data={yearly_data} keyword={keyword} />
                    </div>

                    <div className="card full-width">
                        <div className="card-header">
                            <span className="card-title">📋 年度別出題一覧</span>
                            <span className="card-subtitle">過去{yearly_data.length}年間のデータ</span>
                        </div>
                        <FrequencyTable data={yearly_data} keyword={keyword} />
                    </div>
                </div>
            </div>
        )
    }

    // Default: overview
    return (
        <div>
            <div className="dashboard-grid">
                <div className="card">
                    <div className="card-header">
                        <span className="card-title">📊 分野別出題比率（全期間）</span>
                    </div>
                    <SubjectBreakdown data={subjectData} />
                </div>

                <div className="card">
                    <div className="card-header">
                        <span className="card-title">📋 分野別出題数</span>
                    </div>
                    {subjectData.length > 0 ? (
                        <table className="data-table">
                            <thead>
                                <tr>
                                    <th>分野</th>
                                    <th>出題数</th>
                                    <th>割合</th>
                                </tr>
                            </thead>
                            <tbody>
                                {subjectData.map((d, i) => (
                                    <tr key={i}>
                                        <td>{d.subject_name}</td>
                                        <td><span className="count-number">{d.count}</span></td>
                                        <td>{d.percentage}%</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    ) : (
                        <div className="loading">データ読み込み中...</div>
                    )}
                </div>
            </div>

            {/* Topic Breakdown - Subcategory Display */}
            <div className="card full-width" style={{ marginTop: '1.5rem' }}>
                <div className="card-header">
                    <span className="card-title">📋 テーマ別出題数（サブカテゴリ × 年度）</span>
                    <span className="card-subtitle">分野をクリックして展開 → テーマをクリックで問題番号を表示</span>
                </div>
                <TopicBreakdownTable data={topicData} />
            </div>

            <div className="empty-state">
                <div className="empty-icon">🔍</div>
                <h3>法律名やテーマを検索してみましょう</h3>
                <p>例：「行政手続法」「抵当権」「不法行為」「取消訴訟」</p>
            </div>
        </div>
    )
}
