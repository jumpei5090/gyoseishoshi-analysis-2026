import { useState, useCallback, useEffect } from 'react'
import Dashboard from './components/Dashboard'
import SearchBar from './components/SearchBar'
import TopicBrowser from './components/TopicBrowser'
import ExportButtons from './components/ExportButtons'
import PredictionPage from './components/PredictionPage'
import QuestionBrowserPage from './components/QuestionBrowserPage'
import AnalyticsPage from './components/AnalyticsPage'
import NicknameModal from './components/NicknameModal'

const NICKNAME_KEY = 'gyoseishoshi_nickname'

export default function App() {
    const [searchResult, setSearchResult] = useState(null)
    const [loading, setLoading] = useState(false)
    const [currentPage, setCurrentPage] = useState('analysis')
    const [initialTopicId, setInitialTopicId] = useState(null) // topic to auto-select in QuestionBrowser
    // nickname that is actively in use this session (null = not yet confirmed)
    const [nickname, setNickname] = useState(null)
    // nickname previously stored in localStorage on this device
    const [savedNickname] = useState(() => localStorage.getItem(NICKNAME_KEY) || '')
    const [showNicknameEdit, setShowNicknameEdit] = useState(false)

    // Show setup/confirm modal on fresh session (nickname not yet confirmed)
    // If device has savedNickname → confirm modal; if not → register modal
    // Either way, shown until user confirms.

    function handleNicknameSave(name) {
        setNickname(name)
        localStorage.setItem(NICKNAME_KEY, name)
        setShowNicknameEdit(false)
    }

    const handleSearch = useCallback((result) => {
        setSearchResult(result)
    }, [])

    // Navigate directly to a topic in QuestionBrowserPage
    const handleNavigateToTopic = useCallback((topicId) => {
        setInitialTopicId(topicId)
        setCurrentPage('browser')
    }, [])

    return (
        <div className="app">
            {/* Nickname modal: shown until nickname confirmed for this session */}
            {(!nickname || showNicknameEdit) && (
                <NicknameModal
                    savedNickname={savedNickname}
                    onSave={handleNicknameSave}
                />
            )}

            <header className="header">
                <div className="header-top">
                    <span className="header-icon">⚖️</span>
                    <h1>行政書士 過去問分析ツール</h1>
                    {/* Nickname indicator */}
                    {nickname && (
                        <button
                            className="nickname-indicator"
                            onClick={() => setShowNicknameEdit(true)}
                            title="ニックネームを変更"
                        >
                            👤 {nickname}
                        </button>
                    )}
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
                <button
                    className={`page-nav-btn ${currentPage === 'browser' ? 'active' : ''}`}
                    onClick={() => setCurrentPage('browser')}
                >
                    📚 過去問ブラウザ
                </button>
                <button
                    className={`page-nav-btn ${currentPage === 'analytics' ? 'active' : ''}`}
                    onClick={() => setCurrentPage('analytics')}
                >
                    📈 学習分析
                </button>
            </nav>

            {currentPage === 'analysis' ? (
                <>
                    <SearchBar onSearch={handleSearch} onLoadingChange={setLoading} onNavigateToTopic={handleNavigateToTopic} />
                    <TopicBrowser onSearch={handleSearch} onLoadingChange={setLoading} onNavigateToTopic={handleNavigateToTopic} />
                    <ExportButtons />
                    <Dashboard searchResult={searchResult} loading={loading} />
                </>
            ) : currentPage === 'prediction' ? (
                <PredictionPage />
            ) : currentPage === 'browser' ? (
                <QuestionBrowserPage nickname={nickname} initialTopicId={initialTopicId} onTopicConsumed={() => setInitialTopicId(null)} />
            ) : (
                <AnalyticsPage nickname={nickname} />
            )}
        </div>
    )
}
