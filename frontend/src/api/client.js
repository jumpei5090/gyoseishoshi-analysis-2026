const API_BASE = '/api';

export async function searchFrequency(keyword, minYear = 2015, maxYear = 2025) {
    const params = new URLSearchParams({ keyword, min_year: minYear, max_year: maxYear });
    const res = await fetch(`${API_BASE}/analysis/frequency?${params}`);
    if (!res.ok) throw new Error('検索に失敗しました');
    return res.json();
}

export async function searchSuggestions(keyword) {
    if (!keyword || keyword.length === 0) return [];
    const res = await fetch(`${API_BASE}/analysis/search?keyword=${encodeURIComponent(keyword)}`);
    if (!res.ok) return [];
    return res.json();
}

export async function getSubjectBreakdown(year = null) {
    const params = year ? `?year=${year}` : '';
    const res = await fetch(`${API_BASE}/analysis/subject-breakdown${params}`);
    if (!res.ok) throw new Error('分野別データの取得に失敗しました');
    return res.json();
}

export async function getHeatmap(subjectId = null, minYear = 2015, maxYear = 2025) {
    const params = new URLSearchParams({ min_year: minYear, max_year: maxYear });
    if (subjectId) params.set('subject_id', subjectId);
    const res = await fetch(`${API_BASE}/analysis/heatmap?${params}`);
    if (!res.ok) throw new Error('ヒートマップデータの取得に失敗しました');
    return res.json();
}

export async function getSubjects() {
    const res = await fetch(`${API_BASE}/analysis/subjects`);
    if (!res.ok) throw new Error('分野一覧の取得に失敗しました');
    return res.json();
}

export function getExportCsvUrl(subjectId = null, minYear = 2015, maxYear = 2025) {
    const params = new URLSearchParams({ min_year: minYear, max_year: maxYear });
    if (subjectId) params.set('subject_id', subjectId);
    return `${API_BASE}/export/csv?${params}`;
}

export async function getTaxonomy() {
    const res = await fetch(`${API_BASE}/analysis/taxonomy`);
    if (!res.ok) throw new Error('分類データの取得に失敗しました');
    return res.json();
}

export async function getQuestions(keyword, year) {
    const params = new URLSearchParams({ keyword, year });
    const res = await fetch(`${API_BASE}/analysis/questions?${params}`);
    if (!res.ok) throw new Error('問題データの取得に失敗しました');
    return res.json();
}

export async function getTopicPredictions() {
    const res = await fetch(`${API_BASE}/analysis/predictions/topics`);
    if (!res.ok) throw new Error('予測データの取得に失敗しました');
    return res.json();
}

export async function getLawPredictions() {
    const res = await fetch(`${API_BASE}/analysis/predictions/laws`);
    if (!res.ok) throw new Error('予測データの取得に失敗しました');
    return res.json();
}

export async function getTopicBreakdown(minYear = 2015, maxYear = 2025) {
    const params = new URLSearchParams({ min_year: minYear, max_year: maxYear });
    const res = await fetch(`${API_BASE}/analysis/topic-breakdown?${params}`);
    if (!res.ok) throw new Error('トピック別データの取得に失敗しました');
    return res.json();
}

export async function getSingleQuestion(year, questionNumber) {
    const res = await fetch(`${API_BASE}/analysis/question/${year}/${questionNumber}`);
    if (!res.ok) throw new Error('問題データの取得に失敗しました');
    return res.json();
}

export async function getQuestionsByTopic(topicId, minYear = 2015, maxYear = 2025) {
    const params = new URLSearchParams({ topic_id: topicId, min_year: minYear, max_year: maxYear });
    const res = await fetch(`${API_BASE}/analysis/questions-by-topic?${params}`);
    if (!res.ok) throw new Error('問題データの取得に失敗しました');
    return res.json();
}

// === Answer History ===

export async function saveAnswer(nickname, questionId, isCorrect, mode = 'practice') {
    const params = new URLSearchParams({
        nickname,
        question_id: questionId,
        is_correct: isCorrect,
        mode,
    });
    const res = await fetch(`${API_BASE}/answers?${params}`, { method: 'POST' });
    if (!res.ok) throw new Error('回答の保存に失敗しました');
    return res.json();
}

export async function getHistory(nickname) {
    if (!nickname) return [];
    const res = await fetch(`${API_BASE}/answers/${encodeURIComponent(nickname)}/history`);
    if (!res.ok) return [];
    const list = await res.json();
    // Convert to map: question_id → { is_correct, answered_at, mode }
    const map = {};
    for (const item of list) {
        map[item.question_id] = item;
    }
    return map;
}

export async function getAnalysis(nickname) {
    if (!nickname) return null;
    const res = await fetch(`${API_BASE}/answers/${encodeURIComponent(nickname)}/analysis`);
    if (!res.ok) throw new Error('分析データの取得に失敗しました');
    return res.json();
}
