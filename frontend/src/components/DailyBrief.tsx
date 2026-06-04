import { useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'

interface DashboardData {
  generated_on: string
  top_streamer: { name: string; tier: string; mlb_team: string; recommendation: { action: string } } | null
  top_waiver_drop: { name: string; mlb_team: string; recommendation: { action: string; reason: string } } | null
  pitcher_starts: {
    team: string | null
    probable_roster_count: number
    recommended_rows: { name: string; tier: string; slot: string }[]
    suggested_moves: string[]
  }
  weekly_scores: {
    period: number
    my_team: { team_name: string; score: number; rank: number; half: string } | null
    median_score: number
    mean_score: number
  }
}

function Pill({ label, color }: { label: string; color: string }) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {label}
    </span>
  )
}

function halfColor(half: string) {
  return half === 'top' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'
}

export default function DailyBrief() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.dashboard()
      .then(d => setData(d as DashboardData))
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Card title="Daily Brief" loading={loading} error={error} className="col-span-1 lg:col-span-2">
      {data && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">

          <div className="flex flex-col gap-1">
            <span className="text-xs text-gray-500">Top Streamer</span>
            {data.top_streamer ? (
              <>
                <span className="font-semibold text-white">{data.top_streamer.name}</span>
                <span className="text-xs text-gray-400">{data.top_streamer.mlb_team} · {data.top_streamer.tier}</span>
                <Pill label={data.top_streamer.recommendation.action} color="bg-blue-900 text-blue-300" />
              </>
            ) : <span className="text-gray-500 text-sm">None today</span>}
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-xs text-gray-500">Top Waiver Drop</span>
            {data.top_waiver_drop ? (
              <>
                <span className="font-semibold text-white">{data.top_waiver_drop.name}</span>
                <span className="text-xs text-gray-400">{data.top_waiver_drop.mlb_team}</span>
                <Pill label={data.top_waiver_drop.recommendation.action} color="bg-yellow-900 text-yellow-300" />
              </>
            ) : <span className="text-gray-500 text-sm">None</span>}
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-xs text-gray-500">Pitcher Starts</span>
            <span className="font-semibold text-white">
              {data.pitcher_starts.probable_roster_count} probable
            </span>
            {data.pitcher_starts.recommended_rows.slice(0, 2).map(r => (
              <span key={r.name} className="text-xs text-gray-300">{r.name} · {r.tier}</span>
            ))}
            {data.pitcher_starts.suggested_moves.slice(0, 1).map((m, i) => (
              <span key={i} className="text-xs text-orange-400">{m}</span>
            ))}
          </div>

          <div className="flex flex-col gap-1">
            <span className="text-xs text-gray-500">Weekly Score</span>
            {data.weekly_scores.my_team ? (
              <>
                <span className="font-semibold text-white">{data.weekly_scores.my_team.score.toFixed(1)} pts</span>
                <span className="text-xs text-gray-400">
                  Rank {data.weekly_scores.my_team.rank} · Wk {data.weekly_scores.period}
                </span>
                <Pill
                  label={data.weekly_scores.my_team.half === 'top' ? 'Top Half' : 'Bottom Half'}
                  color={halfColor(data.weekly_scores.my_team.half)}
                />
                <span className="text-xs text-gray-500">Med {data.weekly_scores.median_score}</span>
              </>
            ) : <span className="text-gray-500 text-sm">Unavailable</span>}
          </div>

        </div>
      )}
    </Card>
  )
}
