import { useState } from 'react'
import QuestionModal from './QuestionModal'

export default function FrequencyTable({ data, keyword }) {
    const [modalTarget, setModalTarget] = useState(null)

    if (!data || data.length === 0) return null

    const maxCount = Math.max(...data.map(d => d.count), 1)

    return (
        <>
            <table className="data-table">
                <thead>
                    <tr>
                        <th>年度</th>
                        <th>出題数</th>
                        <th style={{ width: '50%' }}>分布</th>
                    </tr>
                </thead>
                <tbody>
                    {data.map(d => (
                        <tr key={d.year}>
                            <td>{d.year}年</td>
                            <td>
                                {d.count > 0 ? (
                                    <span
                                        className="count-number clickable"
                                        onClick={() => setModalTarget({ year: d.year, count: d.count })}
                                        title={`${d.year}年の問題を表示`}
                                    >
                                        {d.count}
                                    </span>
                                ) : (
                                    <span className="count-number zero">0</span>
                                )}
                            </td>
                            <td>
                                <div className="count-bar">
                                    <div
                                        className="count-bar-fill"
                                        style={{ width: `${(d.count / maxCount) * 100}%`, minWidth: d.count > 0 ? '8px' : '0' }}
                                    />
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            {modalTarget && keyword && (
                <QuestionModal
                    year={modalTarget.year}
                    keyword={keyword}
                    onClose={() => setModalTarget(null)}
                />
            )}
        </>
    )
}
