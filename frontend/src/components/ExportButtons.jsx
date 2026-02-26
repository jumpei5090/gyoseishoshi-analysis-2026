import { getExportCsvUrl } from '../api/client'

export default function ExportButtons() {
    const handleCsvExport = () => {
        const url = getExportCsvUrl()
        window.open(url, '_blank')
    }

    return (
        <div className="export-section">
            <button className="btn btn-outline" onClick={handleCsvExport}>
                📥 CSV ダウンロード
            </button>
        </div>
    )
}
