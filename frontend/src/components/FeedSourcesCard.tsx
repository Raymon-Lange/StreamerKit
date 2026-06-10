import { useCallback, useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'

interface FeedSource {
  key: string
  status: 'fresh' | 'stale' | 'missing'
  age_seconds: number | null
  ttl_seconds: number | null
  last_url: string | null
  fetched_at: string | null
  last_error_type: string | null
  last_error_message: string | null
  last_error_at: string | null
}

function ageStr(seconds: number): string {
  if (seconds < 60) return `${Math.floor(seconds)}s ago`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h ago`
  return `${(seconds / 86400).toFixed(1)}d ago`
}

function ttlStr(ttl: number | null): string {
  if (ttl === null) return 'permanent'
  const days = ttl / 86400
  if (days >= 1) return `${Math.round(days)}d`
  return `${Math.round(ttl / 3600)}h`
}

function tsStr(ts: string | null): string {
  if (!ts) return ''
  try {
    return new Date(ts).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return ts
  }
}

const statusStyles: Record<string, { dot: string; label: string; text: string }> = {
  fresh:   { dot: 'bg-green-500',  label: 'fresh',   text: 'text-green-400' },
  stale:   { dot: 'bg-yellow-500', label: 'stale',   text: 'text-yellow-400' },
  missing: { dot: 'bg-red-500',    label: 'missing',  text: 'text-red-400' },
}

export default function FeedSourcesCard() {
  const [sources, setSources] = useState<FeedSource[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(() => {
    setLoading(true)
    setError(null)
    api.feedStatus()
      .then(d => setSources(((d as { sources: FeedSource[] }).sources ?? [])))
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => { load() }, [load])

  return (
    <Card
      title="Feed Sources"
      loading={loading}
      error={error}
    >
      <div className="flex justify-end">
        <button
          onClick={load}
          className="text-xs text-gray-500 hover:text-gray-300 transition-colors px-2 py-1 rounded border border-gray-700 hover:border-gray-500"
        >
          Refresh
        </button>
      </div>
      <div className="flex flex-col gap-3">
        {sources.map(src => {
          const style = statusStyles[src.status] ?? statusStyles.missing
          return (
            <div key={src.key} className="flex flex-col gap-0.5 border-b border-gray-800 pb-3 last:border-0 last:pb-0">
              <div className="flex items-center gap-2">
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${style.dot}`} />
                <span className="text-sm font-mono text-gray-200">{src.key}</span>
                <span className={`text-xs ml-auto ${style.text}`}>{style.label}</span>
              </div>
              <div className="pl-4 text-xs text-gray-500 flex flex-wrap gap-x-4 gap-y-0.5">
                {src.age_seconds !== null && (
                  <span>{ageStr(src.age_seconds)} · TTL {ttlStr(src.ttl_seconds)}</span>
                )}
                {src.age_seconds === null && <span>no cache entry</span>}
                {src.last_url && (
                  <a href={src.last_url} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline truncate max-w-xs">
                    source ↗
                  </a>
                )}
              </div>
              {src.last_error_type && (
                <div className="pl-4 text-xs text-red-400">
                  ✗ {src.last_error_type}: {src.last_error_message}
                  {src.last_error_at && <span className="text-gray-600 ml-1">({tsStr(src.last_error_at)})</span>}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}
