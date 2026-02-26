import { useState, useEffect, useRef } from 'react'
import { searchFrequency, searchSuggestions } from '../api/client'

export default function SearchBar({ onSearch, onLoadingChange }) {
    const [query, setQuery] = useState('')
    const [suggestions, setSuggestions] = useState([])
    const [showSuggestions, setShowSuggestions] = useState(false)
    const debounceRef = useRef(null)
    const wrapperRef = useRef(null)

    // Close suggestions on outside click
    useEffect(() => {
        function handleClick(e) {
            if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
                setShowSuggestions(false)
            }
        }
        document.addEventListener('mousedown', handleClick)
        return () => document.removeEventListener('mousedown', handleClick)
    }, [])

    // Debounce suggestions
    useEffect(() => {
        if (debounceRef.current) clearTimeout(debounceRef.current)
        if (!query.trim()) {
            setSuggestions([])
            return
        }
        debounceRef.current = setTimeout(async () => {
            const results = await searchSuggestions(query.trim())
            setSuggestions(results)
            setShowSuggestions(results.length > 0)
        }, 300)
        return () => clearTimeout(debounceRef.current)
    }, [query])

    const doSearch = async (keyword) => {
        if (!keyword.trim()) return
        setShowSuggestions(false)
        onLoadingChange(true)
        try {
            const result = await searchFrequency(keyword.trim())
            onSearch(result)
        } catch (err) {
            console.error(err)
        } finally {
            onLoadingChange(false)
        }
    }

    const handleSubmit = (e) => {
        e.preventDefault()
        doSearch(query)
    }

    const handleSuggestionClick = (item) => {
        setQuery(item.name)
        doSearch(item.name)
    }

    const badgeClass = (type) => {
        const map = { subject: 'badge-subject', law: 'badge-law', topic: 'badge-topic' }
        return `suggestion-badge ${map[type] || ''}`
    }

    const badgeLabel = (type) => {
        const map = { subject: '分野', law: '法律', topic: 'テーマ' }
        return map[type] || type
    }

    return (
        <div className="search-container" ref={wrapperRef}>
            <form onSubmit={handleSubmit}>
                <div className="search-wrapper">
                    <span className="search-icon">🔍</span>
                    <input
                        className="search-input"
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
                        placeholder="法律名やテーマを入力（例：行政手続法、抵当権、不法行為）"
                    />
                </div>
            </form>

            {showSuggestions && (
                <div className="suggestions">
                    {suggestions.map((item, i) => (
                        <div key={i} className="suggestion-item" onClick={() => handleSuggestionClick(item)}>
                            <span className={badgeClass(item.type)}>{badgeLabel(item.type)}</span>
                            <span className="suggestion-name">{item.name}</span>
                            {item.parent_name && <span className="suggestion-parent">{item.parent_name}</span>}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
