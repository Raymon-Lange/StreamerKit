import { useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'

interface LastStart {
  date: string
  matchup: string
  result: string
  ip: string
  h: number
  er: number
  k: number
}

interface StreamerRow {
  name: string
  mlb_team: string
  tier: string
  streamer_rank: number | null
  percent_owned: number | null
  injury_status: string | null
  recommendation: { action: string; reason: string; score?: number }
  season_record: string | null
  last_ten_record: string | null
  last_two_starts: LastStart[]
  opponent_team: string | null
  opponent_score: number | null
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

function dateLabel(offset: number) {
  const d = new Date()
  d.setDate(d.getDate() + offset)
  return `${DAYS[d.getDay()]} ${d.getDate()}`
}

interface Props {
  tomorrow?: boolean
}

export default function StreamerCard({ tomorrow = false }: Props) {
  const [rows, setRows] = useState<StreamerRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedName, setExpandedName] = useState<string | null>(null)

  useEffect(() => {
    api.streamers(tomorrow)
      .then(d => setRows(((d as { rows: StreamerRow[] }).rows ?? []).slice(0, 8)))
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [tomorrow])

  const title = tomorrow
    ? `Tomorrow's SP Streamers · ${dateLabel(1)}`
    : `SP Streamers · ${dateLabel(0)}`

  const emptyMsg = tomorrow ? 'No streamers tomorrow.' : 'No streamers today.'

  return (
    <Card title={title} loading={loading} error={error}>
      <div className="flex flex-col divide-y divide-gray-800">
        {rows.map(r => (
          <div
            key={r.name}
            className="py-2 cursor-pointer select-none"
            onClick={() => setExpandedName(prev => prev === r.name ? null : r.name)}
          >
            <div className="flex items-start justify-between gap-2">
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
                <span
                  className="inline-block text-gray-500 text-xs"
                  style={{ transition: 'transform 150ms', transform: expandedName === r.name ? 'rotate(90deg)' : 'rotate(0deg)' }}
                >›</span>
              </div>
            </div>
            {expandedName === r.name && (
              <div className="mt-2 pt-2 border-t border-gray-800 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                <span className="text-gray-600">Season</span>
                <span className="text-gray-300">{r.season_record ?? '—'}</span>
                <span className="text-gray-600">Last 10</span>
                <span className="text-gray-300">{r.last_ten_record ?? '—'}</span>
                <span className="text-gray-600">Last 2</span>
                <span className="text-gray-300">
                  {r.last_two_starts.length === 0 ? '—' : r.last_two_starts.map((s, i) => (
                    <span key={i} className="block">{s.result} · {s.ip} IP · {s.k}K · {s.er} ER ({s.matchup})</span>
                  ))}
                </span>
                <span className="text-gray-600">Opponent</span>
                <span className="text-gray-300">
                  {r.opponent_team ?? '—'}{r.opponent_score != null ? ` (${r.opponent_score})` : ''}
                </span>
              </div>
            )}
          </div>
        ))}
        {rows.length === 0 && !loading && !error && (
          <p className="text-gray-500 text-sm">{emptyMsg}</p>
        )}
      </div>
    </Card>
  )
}
