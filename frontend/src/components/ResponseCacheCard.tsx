import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'

interface CacheEntry {
  key: string
  age_seconds: number
  ttl_seconds: number
  remaining_seconds: number
}

function ageStr(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  return `${(seconds / 3600).toFixed(1)}h ago`
}

function remainingStr(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s left`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m left`
  return `${(seconds / 3600).toFixed(1)}h left`
}

function freshnessBar(remaining: number, total: number): number {
  return Math.max(0, Math.min(100, (remaining / total) * 100))
}

export default function ResponseCacheCard() {
  const [entries, setEntries] = useState<CacheEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    api.feedStatus()
      .then(d => setEntries(((d as { response_cache: CacheEntry[] }).response_cache ?? [])))
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <Card title="API Response Cache" loading={loading} error={error}>
      <div className="flex justify-end">
        <button
          onClick={load}
          className="text-xs text-gray-500 hover:text-gray-300 transition-colors px-2 py-1 rounded border border-gray-700 hover:border-gray-500"
        >
          Refresh
        </button>
      </div>
      {entries.length === 0 ? (
        <p className="text-sm text-gray-600 italic">Cache is cold — no active entries.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {entries.map(e => {
            const pct = freshnessBar(e.remaining_seconds, e.ttl_seconds)
            return (
              <div key={e.key} className="flex flex-col gap-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-mono text-gray-300 truncate">{e.key}</span>
                  <span className="text-xs text-gray-500 flex-shrink-0">{remainingStr(e.remaining_seconds)}</span>
                </div>
                <div className="w-full h-1 bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-600 rounded-full transition-all"
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="text-xs text-gray-600">{ageStr(e.age_seconds)}</span>
              </div>
            )
          })}
        </div>
      )}
    </Card>
  )
}
