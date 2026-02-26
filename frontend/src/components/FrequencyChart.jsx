import { useRef, useEffect } from 'react'
import { Chart, registerables } from 'chart.js'

Chart.register(...registerables)

export default function FrequencyChart({ data, keyword }) {
    const canvasRef = useRef(null)
    const chartRef = useRef(null)

    useEffect(() => {
        if (!data || data.length === 0) return

        if (chartRef.current) chartRef.current.destroy()

        const ctx = canvasRef.current.getContext('2d')

        // Gradient fill
        const gradient = ctx.createLinearGradient(0, 0, 0, 300)
        gradient.addColorStop(0, 'rgba(88, 166, 255, 0.3)')
        gradient.addColorStop(1, 'rgba(88, 166, 255, 0.02)')

        chartRef.current = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => `${d.year}年`),
                datasets: [
                    {
                        label: `${keyword} 出題数`,
                        data: data.map(d => d.count),
                        backgroundColor: gradient,
                        borderColor: 'rgba(88, 166, 255, 0.8)',
                        borderWidth: 2,
                        borderRadius: 6,
                        borderSkipped: false,
                    },
                    {
                        label: 'トレンド',
                        data: data.map(d => d.count),
                        type: 'line',
                        borderColor: '#a371f7',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointBackgroundColor: '#a371f7',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 1,
                        pointRadius: 4,
                        pointHoverRadius: 6,
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
                            font: { family: 'Noto Sans JP', size: 12 },
                            usePointStyle: true,
                            padding: 20,
                        },
                    },
                    tooltip: {
                        backgroundColor: '#1c2128',
                        titleColor: '#e6edf3',
                        bodyColor: '#8b949e',
                        borderColor: '#30363d',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        titleFont: { family: 'Noto Sans JP' },
                        bodyFont: { family: 'Noto Sans JP' },
                        callbacks: {
                            label: (ctx) => `${ctx.dataset.label}: ${ctx.parsed.y} 問`,
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(48, 54, 61, 0.5)', drawBorder: false },
                        ticks: { color: '#8b949e', font: { family: 'Noto Sans JP', size: 12 } },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(48, 54, 61, 0.5)', drawBorder: false },
                        ticks: {
                            color: '#8b949e',
                            font: { family: 'Noto Sans JP', size: 12 },
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
    }, [data, keyword])

    return (
        <div className="chart-container">
            <canvas ref={canvasRef}></canvas>
        </div>
    )
}
