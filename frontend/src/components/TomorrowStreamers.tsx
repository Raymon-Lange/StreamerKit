import { useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'

interface StreamerRow {
  name: string
  mlb_team: string
  tier: string
  streamer_rank: number | null
  percent_owned: number | null
  recommendation: { action: string; reason: string }
}

const tierColor: Record<string, string> = {
  'Must Stream': 'text-green-400',
  'Strong Stream': 'text-blue-400',
  'Streamer': 'text-yellow-400',
  'Deep League': 'text-orange-400',
  'Not Ranked': 'text-gray-500',
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function tomorrowLabel() {
  const d = new Date()
  d.setDate(d.getDate() + 1)
  return `${DAYS[d.getDay()]} ${d.getDate()}`
}

export default function TomorrowStreamers() {
  const [rows, setRows] = useState<StreamerRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.streamers(true)
      .then(d => setRows(((d as { rows: StreamerRow[] }).rows ?? []).slice(0, 8)))
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Card title={`Tomorrow's SP Streamers · ${tomorrowLabel()}`} loading={loading} error={error}>
      <div className="flex flex-col divide-y divide-gray-800">
        {rows.map(r => (
          <div key={r.name} className="py-2 flex items-start justify-between gap-2">
            <div className="flex flex-col gap-0.5 min-w-0">
              <span className="font-medium text-white text-sm truncate">{r.name}</span>
              <span className="text-xs text-gray-400">{r.mlb_team} · {r.percent_owned != null ? `${r.percent_owned.toFixed(0)}% owned` : ''}</span>
              <span className="text-xs text-gray-500 truncate">{r.recommendation.reason}</span>
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              <span className={`text-xs font-semibold ${tierColor[r.tier] ?? 'text-gray-400'}`}>{r.tier}</span>
              <span className="text-xs text-gray-500">{r.streamer_rank != null ? `#${r.streamer_rank}` : 'NR'}</span>
            </div>
          </div>
        ))}
        {rows.length === 0 && !loading && !error && <p className="text-gray-500 text-sm">No streamers tomorrow.</p>}
      </div>
    </Card>
  )
}
