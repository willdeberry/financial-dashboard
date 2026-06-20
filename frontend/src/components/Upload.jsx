import { useState } from 'react'
import { api } from '../api.js'

const SOURCE_OPTIONS = [
  { value: 'bank', label: 'Bank Statement', icon: '🏦' },
  { value: 'credit_card', label: 'Credit Card', icon: '💳' },
  { value: 'payroll', label: 'Pay Stub', icon: '💵' },
]

export default function Upload({ onSuccess }) {
  const [file, setFile] = useState(null)
  const [sourceType, setSourceType] = useState('bank')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [dragOver, setDragOver] = useState(false)

  const setFileClean = (f) => {
    if (f && !f.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported.')
      return
    }
    setFile(f)
    setResult(null)
    setError(null)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragOver(false)
    setFileClean(e.dataTransfer.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await api.uploadFile(file, sourceType)
      setResult(res)
      if (res.status === 'processed') setTimeout(onSuccess, 1800)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-xl mx-auto">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">Upload Statement</h2>
      <form onSubmit={handleSubmit} className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 space-y-6">

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Statement Type</label>
          <div className="grid grid-cols-3 gap-3">
            {SOURCE_OPTIONS.map(opt => (
              <label
                key={opt.value}
                className={`flex flex-col items-center justify-center gap-1 px-3 py-4 rounded-xl border-2 cursor-pointer transition-all text-center ${
                  sourceType === opt.value
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 text-gray-600 dark:text-gray-400'
                }`}
              >
                <input
                  type="radio"
                  name="sourceType"
                  value={opt.value}
                  checked={sourceType === opt.value}
                  onChange={() => setSourceType(opt.value)}
                  className="sr-only"
                />
                <span className="text-2xl">{opt.icon}</span>
                <span className="text-xs font-medium">{opt.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div
          onDragOver={e => { e.preventDefault(); setDragOver(true) }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-xl p-10 text-center transition-all ${
            dragOver
              ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20'
              : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500 bg-gray-50 dark:bg-gray-750'
          }`}
        >
          <div className="text-4xl mb-3">📄</div>
          {file ? (
            <div>
              <p className="font-medium text-gray-900 dark:text-white text-sm">{file.name}</p>
              <p className="text-xs text-gray-400 mt-1">{(file.size / 1024).toFixed(0)} KB</p>
            </div>
          ) : (
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Drop your PDF here or</p>
              <label className="cursor-pointer text-blue-600 dark:text-blue-400 text-sm font-medium hover:underline">
                browse
                <input type="file" accept=".pdf" onChange={e => setFileClean(e.target.files[0])} className="sr-only" />
              </label>
            </div>
          )}
        </div>

        {file && (
          <button
            type="button"
            onClick={() => setFile(null)}
            className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            × Remove file
          </button>
        )}

        {error && (
          <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 text-sm text-red-700 dark:text-red-400">
            {error}
          </div>
        )}

        {result && (
          <div className={`rounded-lg p-4 text-sm border ${
            result.status === 'processed'
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800 text-green-700 dark:text-green-400'
              : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-700 dark:text-red-400'
          }`}>
            {result.status === 'processed'
              ? `✓ Imported ${result.transaction_count} transactions from "${result.filename}". Redirecting to dashboard…`
              : `✗ ${result.error_message || 'Processing failed'}`}
          </div>
        )}

        <button
          type="submit"
          disabled={!file || loading}
          className="w-full py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors"
        >
          {loading ? 'Processing…' : 'Upload & Extract Transactions'}
        </button>
      </form>
    </div>
  )
}
