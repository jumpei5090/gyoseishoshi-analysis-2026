import { useRef, useEffect } from 'react'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

const COLORS = [
    'rgba(88, 166, 255, 0.8)',
    'rgba(63, 185, 80, 0.8)',
    'rgba(210, 153, 34, 0.8)',
    'rgba(163, 113, 247, 0.8)',
    'rgba(248, 81, 73, 0.8)',
    'rgba(247, 120, 186, 0.8)',
]

export default function SubjectBreakdown({ data }) {
    const canvasRef = useRef(null)
    const chartRef = useRef(null)

    useEffect(() => {
        if (!data || data.length === 0) return
        if (chartRef.current) chartRef.current.destroy()

        const ctx = canvasRef.current.getContext('2d')

        chartRef.current = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.subject_name),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: COLORS.slice(0, data.length),
                    borderColor: '#1c2128',
                    borderWidth: 3,
                    hoverOffset: 8,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#ffffff', // Pure white for maximum visibility
                            font: { family: 'Noto Sans JP', size: 12 },
                            usePointStyle: true,
                            padding: 16,
                            generateLabels: (chart) => {
                                const ds = chart.data.datasets[0]
                                return chart.data.labels.map((label, i) => ({
                                    text: `${label} (${ds.data[i]}問)`,
                                    fillStyle: ds.backgroundColor[i],
                                    strokeStyle: ds.backgroundColor[i],
                                    pointStyle: 'circle',
                                    index: i,
                                }))
                            },
                        },
                    },
                    tooltip: {
                        backgroundColor: '#1c2128',
                        titleColor: '#e6edf3',
                        bodyColor: '#8b949e',
                        borderColor: '#30363d',
                        borderWidth: 1,
                        cornerRadius: 8,
                        callbacks: {
                            label: (ctx) => {
                                const d = data[ctx.dataIndex]
                                return ` ${d.subject_name}: ${d.count}問 (${d.percentage}%)`
                            },
                        },
                    },
                },
            },
        })

        return () => { if (chartRef.current) chartRef.current.destroy() }
    }, [data])

    return (
        <div className="chart-container">
            <canvas ref={canvasRef}></canvas>
        </div>
    )
}
