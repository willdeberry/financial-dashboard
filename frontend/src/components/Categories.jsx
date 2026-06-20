import { useState, useEffect } from 'react'
import { api } from '../api.js'

const DEFAULT_COLORS = [
  '#ef4444', '#f97316', '#eab308', '#22c55e', '#14b8a6',
  '#3b82f6', '#8b5cf6', '#ec4899', '#6b7280', '#0ea5e9',
]

function ColorDot({ color, size = 'w-4 h-4' }) {
  return (
    <span
      className={`inline-block rounded-full flex-shrink-0 ${size}`}
      style={{ backgroundColor: color || '#9ca3af' }}
    />
  )
}

function EditModal({ category, categories, onSave, onClose }) {
  const [name, setName] = useState(category.name)
  const [color, setColor] = useState(category.color || '#6b7280')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleSave() {
    if (!name.trim()) { setError('Name is required'); return }
    setSaving(true)
    setError('')
    try {
      const updated = await api.updateCategory(category.id, { name: name.trim(), color })
      onSave(updated)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <h2 className="font-semibold text-gray-900 dark:text-white text-lg">Edit Category</h2>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
          <input
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSave()}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Color</label>
          <div className="flex flex-wrap gap-2 mb-2">
            {DEFAULT_COLORS.map(c => (
              <button
                key={c}
                onClick={() => setColor(c)}
                className={`w-7 h-7 rounded-full border-2 transition-transform ${color === c ? 'border-gray-900 dark:border-white scale-110' : 'border-transparent'}`}
                style={{ backgroundColor: c }}
              />
            ))}
          </div>
          <div className="flex items-center gap-2">
            <input
              type="color"
              value={color}
              onChange={e => setColor(e.target.value)}
              className="w-8 h-8 rounded cursor-pointer border border-gray-300 dark:border-gray-600"
            />
            <span className="text-xs text-gray-500 dark:text-gray-400">Custom</span>
          </div>
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <div className="flex gap-3 justify-end pt-1">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  )
}

function DeleteModal({ category, categories, onDelete, onClose }) {
  const hasTransactions = category.transaction_count > 0
  const others = categories.filter(c => c.id !== category.id)
  const [reassignTo, setReassignTo] = useState(others[0]?.id ?? '')
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')

  async function handleDelete() {
    setDeleting(true)
    setError('')
    try {
      await api.deleteCategory(category.id, hasTransactions ? reassignTo : undefined)
      onDelete(category.id)
    } catch (e) {
      setError(e.message)
    } finally {
      setDeleting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <h2 className="font-semibold text-gray-900 dark:text-white text-lg">Delete Category</h2>

        <p className="text-sm text-gray-600 dark:text-gray-400">
          Delete <span className="font-medium text-gray-900 dark:text-white">{category.name}</span>
          {hasTransactions && (
            <> with <span className="font-medium">{category.transaction_count}</span> transaction{category.transaction_count !== 1 ? 's' : ''}</>
          )}?
        </p>

        {hasTransactions && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Move transactions to
            </label>
            <select
              value={reassignTo}
              onChange={e => setReassignTo(Number(e.target.value))}
              className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {others.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>
          </div>
        )}

        {error && <p className="text-sm text-red-500">{error}</p>}

        <div className="flex gap-3 justify-end pt-1">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            {deleting ? 'Deleting…' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  )
}

function MoveModal({ category, categories, onMove, onClose }) {
  const others = categories.filter(c => c.id !== category.id)
  const [targetId, setTargetId] = useState(others[0]?.id ?? '')
  const [moving, setMoving] = useState(false)
  const [error, setError] = useState('')

  async function handleMove() {
    setMoving(true)
    setError('')
    try {
      await api.moveTransactions(category.id, Number(targetId))
      onMove(category.id, Number(targetId))
    } catch (e) {
      setError(e.message)
    } finally {
      setMoving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-sm p-6 space-y-4">
        <h2 className="font-semibold text-gray-900 dark:text-white text-lg">Move Transactions</h2>

        <p className="text-sm text-gray-600 dark:text-gray-400">
          Move all <span className="font-medium">{category.transaction_count}</span> transaction{category.transaction_count !== 1 ? 's' : ''} from{' '}
          <span className="font-medium text-gray-900 dark:text-white">{category.name}</span> to:
        </p>

        <select
          value={targetId}
          onChange={e => setTargetId(e.target.value)}
          className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {others.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <div className="flex gap-3 justify-end pt-1">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleMove}
            disabled={moving || !targetId}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {moving ? 'Moving…' : 'Move'}
          </button>
        </div>
      </div>
    </div>
  )
}

function NewCategoryForm({ onCreated, onCancel }) {
  const [name, setName] = useState('')
  const [color, setColor] = useState(DEFAULT_COLORS[0])
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function handleCreate() {
    if (!name.trim()) { setError('Name is required'); return }
    setSaving(true)
    setError('')
    try {
      const created = await api.createCategory({ name: name.trim(), color })
      onCreated(created)
    } catch (e) {
      setError(e.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl p-4 space-y-3">
      <h3 className="font-medium text-gray-900 dark:text-white text-sm">New Category</h3>
      <div className="flex gap-3 items-start">
        <div className="flex-1">
          <input
            autoFocus
            placeholder="Category name"
            className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={name}
            onChange={e => setName(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleCreate()}
          />
        </div>
        <div className="flex flex-wrap gap-1.5 max-w-[180px]">
          {DEFAULT_COLORS.map(c => (
            <button
              key={c}
              onClick={() => setColor(c)}
              className={`w-6 h-6 rounded-full border-2 transition-transform ${color === c ? 'border-gray-900 dark:border-white scale-110' : 'border-transparent'}`}
              style={{ backgroundColor: c }}
            />
          ))}
          <input
            type="color"
            value={color}
            onChange={e => setColor(e.target.value)}
            className="w-6 h-6 rounded cursor-pointer border border-gray-300 dark:border-gray-600"
            title="Custom color"
          />
        </div>
      </div>
      {error && <p className="text-xs text-red-500">{error}</p>}
      <div className="flex gap-2 justify-end">
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleCreate}
          disabled={saving}
          className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {saving ? 'Creating…' : 'Create'}
        </button>
      </div>
    </div>
  )
}

export default function Categories() {
  const [categories, setCategories] = useState([])
  const [loading, setLoading] = useState(true)
  const [showNew, setShowNew] = useState(false)
  const [editing, setEditing] = useState(null)
  const [deleting, setDeleting] = useState(null)
  const [moving, setMoving] = useState(null)

  useEffect(() => {
    api.getCategories().then(data => {
      setCategories(data)
      setLoading(false)
    })
  }, [])

  function handleCreated(cat) {
    setCategories(prev => [...prev, cat].sort((a, b) => a.name.localeCompare(b.name)))
    setShowNew(false)
  }

  function handleSaved(updated) {
    setCategories(prev => prev.map(c => c.id === updated.id ? { ...c, ...updated } : c).sort((a, b) => a.name.localeCompare(b.name)))
    setEditing(null)
  }

  function handleDeleted(id) {
    setCategories(prev => prev.filter(c => c.id !== id))
    setDeleting(null)
  }

  function handleMoved(fromId, toId) {
    setCategories(prev => {
      const from = prev.find(c => c.id === fromId)
      const to = prev.find(c => c.id === toId)
      return prev.map(c => {
        if (c.id === fromId) return { ...c, transaction_count: 0 }
        if (c.id === toId) return { ...c, transaction_count: (c.transaction_count || 0) + (from?.transaction_count || 0) }
        return c
      })
    })
    setMoving(null)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">Loading…</div>
    )
  }

  return (
    <div className="space-y-4 max-w-2xl">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Categories</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{categories.length} categories</p>
        </div>
        {!showNew && (
          <button
            onClick={() => setShowNew(true)}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            + New Category
          </button>
        )}
      </div>

      {showNew && (
        <NewCategoryForm onCreated={handleCreated} onCancel={() => setShowNew(false)} />
      )}

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
        {categories.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">No categories yet</div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 dark:border-gray-700">
                <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400 w-8"></th>
                <th className="text-left px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Name</th>
                <th className="text-right px-4 py-3 font-medium text-gray-500 dark:text-gray-400">Transactions</th>
                <th className="px-4 py-3 w-36"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {categories.map(cat => (
                <tr key={cat.id} className="hover:bg-gray-50 dark:hover:bg-gray-750 group">
                  <td className="px-4 py-3">
                    <ColorDot color={cat.color} />
                  </td>
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-white">
                    {cat.name}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-500 dark:text-gray-400">
                    {cat.transaction_count ?? 0}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                      {(cat.transaction_count ?? 0) > 0 && (
                        <button
                          onClick={() => setMoving(cat)}
                          title="Move transactions to another category"
                          className="px-2 py-1 text-xs text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded transition-colors"
                        >
                          Move
                        </button>
                      )}
                      <button
                        onClick={() => setEditing(cat)}
                        className="px-2 py-1 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => setDeleting(cat)}
                        className="px-2 py-1 text-xs text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 rounded transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {editing && (
        <EditModal
          category={editing}
          categories={categories}
          onSave={handleSaved}
          onClose={() => setEditing(null)}
        />
      )}
      {deleting && (
        <DeleteModal
          category={deleting}
          categories={categories}
          onDelete={handleDeleted}
          onClose={() => setDeleting(null)}
        />
      )}
      {moving && (
        <MoveModal
          category={moving}
          categories={categories}
          onMove={handleMoved}
          onClose={() => setMoving(null)}
        />
      )}
    </div>
  )
}
