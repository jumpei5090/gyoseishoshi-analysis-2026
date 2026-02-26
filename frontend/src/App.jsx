import { useState, useCallback } from 'react'
import Dashboard from './components/Dashboard'
import SearchBar from './components/SearchBar'
import TopicBrowser from './components/TopicBrowser'
import ExportButtons from './components/ExportButtons'
import PredictionPage from './components/PredictionPage'

export default function App() {
    const [searchResult, setSearchResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [currentPage, setCurrentPage] = useState('analysis') // 'analysis' or 'prediction'

    const handleSearch = useCallback((result) => {
        setSearchResult(result)
    }, [])

    return (
        <div className="app">
            <header className="header">
                <div className="header-top">
                    <span className="header-icon">⚖️</span>
                    <h1>行政書士 過去問分析ツール</h1>
                </div>
                <p>2026年度（令和8年度）合格目標 ─ 過去10年の出題傾向を瞬時に可視化</p>
            </header>

            {/* Page Navigation */}
            <nav className="page-nav">
                <button
                    className={`page-nav-btn ${currentPage === 'analysis' ? 'active' : ''}`}
                    onClick={() => setCurrentPage('analysis')}
                >
                    📊 出題傾向分析
                </button>
                <button
                    className={`page-nav-btn ${currentPage === 'prediction' ? 'active' : ''}`}
                    onClick={() => setCurrentPage('prediction')}
                >
                    🔮 2026年 出題予測
                </button>
            </nav>

            {currentPage === 'analysis' ? (
                <>
                    <SearchBar onSearch={handleSearch} onLoadingChange={setLoading} />
                    <TopicBrowser onSearch={handleSearch} onLoadingChange={setLoading} />
                    <ExportButtons />
                    <Dashboard searchResult={searchResult} loading={loading} />
                </>
            ) : (
                <PredictionPage />
            )}
        </div>
    )
}
