import { useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'

interface StreamerRow {
  name: string
  mlb_team: string
  tier: string
  streamer_rank: number | null
  percent_owned: number | null
  injury_status: string | null
  recommendation: { action: string; reason: string }
}

const tierColor: Record<string, string> = {
  'Must Stream': 'text-green-400',
  'Strong Stream': 'text-blue-400',
  'Streamer': 'text-yellow-400',
  'Deep League': 'text-orange-400',
  'Not Ranked': 'text-gray-500',
}

const injuryColor: Record<string, string> = {
  TEN_DAY_DL: 'bg-red-900 text-red-300',
  FIFTEEN_DAY_DL: 'bg-red-900 text-red-300',
  SIXTY_DAY_DL: 'bg-red-900 text-red-300',
  SEVEN_DAY_DL: 'bg-red-900 text-red-300',
  INJURY_RESERVE: 'bg-red-900 text-red-300',
  OUT: 'bg-red-900 text-red-300',
  SUSPENSION: 'bg-red-900 text-red-300',
  DAY_TO_DAY: 'bg-orange-900 text-orange-300',
  QUESTIONABLE: 'bg-yellow-900 text-yellow-300',
}

const injuryLabel: Record<string, string> = {
  TEN_DAY_DL: 'IL10',
  FIFTEEN_DAY_DL: 'IL15',
  SIXTY_DAY_DL: 'IL60',
  SEVEN_DAY_DL: 'IL7',
  INJURY_RESERVE: 'IR',
  OUT: 'OUT',
  SUSPENSION: 'SUSP',
  DAY_TO_DAY: 'DTD',
  QUESTIONABLE: 'QUES',
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

function todayLabel() {
  const d = new Date()
  return `${DAYS[d.getDay()]} ${d.getDate()}`
}

export default function Streamers() {
  const [rows, setRows] = useState<StreamerRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.streamers()
      .then(d => setRows(((d as { rows: StreamerRow[] }).rows ?? []).slice(0, 8)))
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Card title={`SP Streamers · ${todayLabel()}`} loading={loading} error={error}>
      <div className="flex flex-col divide-y divide-gray-800">
        {rows.map(r => (
          <div key={r.name} className="py-2 flex items-start justify-between gap-2">
            <div className="flex flex-col gap-0.5 min-w-0">
              <div className="flex items-center gap-1.5">
                <span className="font-medium text-white text-sm truncate">{r.name}</span>
                {r.injury_status && injuryColor[r.injury_status] && (
                  <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium shrink-0 ${injuryColor[r.injury_status]}`}>
                    {injuryLabel[r.injury_status]}
                  </span>
                )}
              </div>
              <span className="text-xs text-gray-400">{r.mlb_team} · {r.percent_owned != null ? `${r.percent_owned.toFixed(0)}% owned` : ''}</span>
              <span className="text-xs text-gray-500 truncate">{r.recommendation.reason}</span>
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              <span className={`text-xs font-semibold ${tierColor[r.tier] ?? 'text-gray-400'}`}>{r.tier}</span>
              <span className="text-xs text-gray-500">{r.streamer_rank != null ? `#${r.streamer_rank}` : 'NR'}</span>
            </div>
          </div>
        ))}
        {rows.length === 0 && <p className="text-gray-500 text-sm">No streamers today.</p>}
      </div>
    </Card>
  )
}
