import { useState } from 'react';

export default function NicknameModal({ savedNickname, onSave }) {
    // 'confirm' mode: device used before → ask to re-use saved nickname
    // 'register' mode: new device → fresh name input
    const [mode, setMode] = useState(savedNickname ? 'confirm' : 'register');
    const [name, setName] = useState('');
    const [error, setError] = useState('');

    function handleConfirm() {
        onSave(savedNickname);
    }

    function handleSubmit(e) {
        e.preventDefault();
        const trimmed = name.trim();
        if (!trimmed) {
            setError('ニックネームを入力してください');
            return;
        }
        if (trimmed.length > 20) {
            setError('20文字以内で入力してください');
            return;
        }
        onSave(trimmed);
    }

    return (
        <div className="modal-overlay">
            <div className="modal-content nickname-modal">
                {mode === 'confirm' ? (
                    <>
                        <div className="nickname-modal-header">
                            <div className="nickname-modal-icon">👤</div>
                            <h2 className="nickname-modal-title">おかえりなさい</h2>
                            <p className="nickname-modal-desc">
                                前回のニックネームでログインしますか？
                            </p>
                            <div className="nickname-saved-display">{savedNickname}</div>
                        </div>
                        <div className="nickname-confirm-actions">
                            <button className="nickname-submit-btn" onClick={handleConfirm}>
                                このニックネームでログイン
                            </button>
                            <button
                                className="nickname-change-btn"
                                onClick={() => setMode('register')}
                            >
                                別のニックネームを使う
                            </button>
                        </div>
                    </>
                ) : (
                    <>
                        <div className="nickname-modal-header">
                            <div className="nickname-modal-icon">👤</div>
                            <h2 className="nickname-modal-title">はじめまして！</h2>
                            <p className="nickname-modal-desc">
                                ニックネームを設定すると、スマホや別のデバイスでも<br />
                                同じ学習履歴・分析データが引き継がれます。
                            </p>
                        </div>
                        <form onSubmit={handleSubmit} className="nickname-form">
                            <input
                                className="nickname-input"
                                type="text"
                                placeholder="ニックネームを入力"
                                value={name}
                                onChange={e => { setName(e.target.value); setError(''); }}
                                autoFocus
                                maxLength={20}
                            />
                            {error && <p className="nickname-error">{error}</p>}
                            <p className="nickname-hint">
                                ※ 同じニックネームを入力することで、どのデバイスでも同じ履歴を利用できます
                            </p>
                            <button type="submit" className="nickname-submit-btn">
                                始める →
                            </button>
                            {savedNickname && (
                                <button
                                    type="button"
                                    className="nickname-change-btn"
                                    onClick={() => setMode('confirm')}
                                >
                                    ← 戻る
                                </button>
                            )}
                        </form>
                    </>
                )}
            </div>
        </div>
    );
}
