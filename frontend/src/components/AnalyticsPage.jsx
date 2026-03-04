import { useState, useEffect } from 'react';
import { getAnalysis } from '../api/client';

function RateBar({ rate, size = 'normal' }) {
    const color = rate >= 70 ? '#3fb950' : rate >= 50 ? '#d29922' : '#f85149';
    return (
        <div className={`analytics-rate-bar-wrap ${size}`}>
            <div
                className="analytics-rate-bar-fill"
                style={{ width: `${rate}%`, background: color }}
            />
        </div>
    );
}

function TopicRow({ topic, rank, type }) {
    const isStrong = type === 'strong';
    return (
        <div className={`analytics-topic-row ${isStrong ? 'strong' : 'weak'}`}>
            <span className="analytics-topic-rank">{rank}</span>
            <div className="analytics-topic-info">
                <span className="analytics-topic-name">{topic.topic_name}</span>
                <span className="analytics-topic-parent">{topic.subject_name} › {topic.law_name}</span>
            </div>
            <div className="analytics-topic-right">
                <RateBar rate={topic.rate} size="small" />
                <span className="analytics-topic-rate" style={{ color: isStrong ? 'var(--success)' : 'var(--danger)' }}>
                    {topic.rate}%
                </span>
                <span className="analytics-topic-count">{topic.answered}問</span>
            </div>
        </div>
    );
}

export default function AnalyticsPage({ nickname }) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        if (!nickname) return;
        setLoading(true);
        setError(null);
        getAnalysis(nickname)
            .then(setData)
            .catch(e => setError(e.message))
            .finally(() => setLoading(false));
    }, [nickname]);

    if (!nickname) {
        return (
            <div className="analytics-page">
                <div className="browser-placeholder">
                    <div className="placeholder-icon">📊</div>
                    <h2>ニックネームを設定してください</h2>
                    <p>右上の「👤」から設定できます</p>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="analytics-page">
                <div className="browser-loading"><div className="spinner" /><span>分析中...</span></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="analytics-page">
                <div className="browser-placeholder">
                    <div className="placeholder-icon">⚠️</div>
                    <h2>データの取得に失敗しました</h2>
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    if (!data || data.total_answered === 0) {
        return (
            <div className="analytics-page">
                <div className="browser-placeholder">
                    <div className="placeholder-icon">📝</div>
                    <h2>まだ回答履歴がありません</h2>
                    <p>「📚 過去問ブラウザ」から問題を解いてみましょう！<br />5肢択一・多肢選択の結果が自動記録されます。</p>
                </div>
            </div>
        );
    }

    const overallRate = data.overall_rate ?? 0;
    const lastDate = data.last_answered_at
        ? new Date(data.last_answered_at).toLocaleString('ja-JP', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
        : '—';

    return (
        <div className="analytics-page">
            {/* Summary */}
            <div className="analytics-summary-grid">
                <div className="analytics-stat-card highlight">
                    <div className="analytics-stat-label">回答問題数</div>
                    <div className="analytics-stat-value">{data.total_answered}<span className="analytics-stat-unit">問</span></div>
                </div>
                <div className="analytics-stat-card">
                    <div className="analytics-stat-label">正解数</div>
                    <div className="analytics-stat-value correct">{data.total_correct}<span className="analytics-stat-unit">問</span></div>
                </div>
                <div className="analytics-stat-card">
                    <div className="analytics-stat-label">不正解数</div>
                    <div className="analytics-stat-value wrong">{data.total_answered - data.total_correct}<span className="analytics-stat-unit">問</span></div>
                </div>
                <div className="analytics-stat-card">
                    <div className="analytics-stat-label">正答率</div>
                    <div className="analytics-stat-value rate">{overallRate}<span className="analytics-stat-unit">%</span></div>
                </div>
                <div className="analytics-stat-card">
                    <div className="analytics-stat-label">最終学習日</div>
                    <div className="analytics-stat-date">{lastDate}</div>
                </div>
            </div>

            {/* Overall progress bar */}
            <div className="analytics-overall-bar-wrap">
                <div className="analytics-overall-bar-label">
                    <span>全体正答率</span>
                    <span style={{ color: overallRate >= 60 ? 'var(--success)' : 'var(--danger)', fontWeight: 700 }}>{overallRate}%</span>
                </div>
                <div className="analytics-rate-bar-wrap">
                    <div
                        className="analytics-rate-bar-fill"
                        style={{
                            width: `${overallRate}%`,
                            background: overallRate >= 60
                                ? 'linear-gradient(90deg, var(--success), #56d364)'
                                : 'linear-gradient(90deg, var(--danger), #ff6b6b)',
                        }}
                    />
                </div>
            </div>

            {/* Subject breakdown */}
            {data.by_subject.length > 0 && (
                <div className="analytics-section">
                    <h2 className="analytics-section-title">📚 分野別正答率</h2>
                    <div className="analytics-subject-list">
                        {data.by_subject.map(s => {
                            const rate = s.rate;
                            return (
                                <div key={s.subject_id} className="analytics-subject-row">
                                    <div className="analytics-subject-name">{s.subject_name}</div>
                                    <div className="analytics-subject-bar-area">
                                        <RateBar rate={rate} />
                                        <span className="analytics-subject-rate"
                                            style={{ color: rate >= 70 ? 'var(--success)' : rate >= 50 ? 'var(--warning)' : 'var(--danger)' }}>
                                            {rate}%
                                        </span>
                                    </div>
                                    <span className="analytics-subject-count">{s.total}問</span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Strong / Weak panels */}
            <div className="analytics-sw-grid">
                <div className="analytics-section">
                    <h2 className="analytics-section-title strong">🏆 得意テーマ Top {data.strong_topics.length}</h2>
                    {data.strong_topics.length === 0 ? (
                        <div className="analytics-no-data">まだ得意テーマが見つかりません<br /><span>同じテーマの問題を2問以上解くと表示されます</span></div>
                    ) : (
                        <div className="analytics-topic-list">
                            {data.strong_topics.map((t, i) => (
                                <TopicRow key={t.topic_id} topic={t} rank={i + 1} type="strong" />
                            ))}
                        </div>
                    )}
                </div>

                <div className="analytics-section">
                    <h2 className="analytics-section-title weak">📌 弱点テーマ Top {data.weak_topics.length}</h2>
                    {data.weak_topics.length === 0 ? (
                        <div className="analytics-no-data">弱点テーマはまだありません 🎉<br /><span>同じテーマの問題を2問以上解くと表示されます</span></div>
                    ) : (
                        <div className="analytics-topic-list">
                            {data.weak_topics.map((t, i) => (
                                <TopicRow key={t.topic_id} topic={t} rank={i + 1} type="weak" />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
