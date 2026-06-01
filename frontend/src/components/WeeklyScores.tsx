import { useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'

interface ScoreRow {
  team_id: number
  team_name: string
  score: number
  rank: number
  half: string
  is_my_team: boolean
}

interface ScoresData {
  period: number
  league: string
  median_score: number
  mean_score: number
  rows: ScoreRow[]
}

export default function WeeklyScores() {
  const [data, setData] = useState<ScoresData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.weeklyScores()
      .then(d => setData(d as ScoresData))
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Card title={data ? `Week ${data.period} Scores` : 'Weekly Scores'} loading={loading} error={error}>
      {data && (
        <div className="flex flex-col gap-1">
          <div className="flex justify-between text-xs text-gray-500 pb-1 border-b border-gray-800">
            <span>Team</span>
            <span>Score</span>
          </div>
          {data.rows.map(r => (
            <div
              key={r.team_id}
              className={`flex justify-between items-center text-sm py-0.5 ${r.is_my_team ? 'text-blue-300 font-semibold' : 'text-gray-300'}`}
            >
              <span className="flex items-center gap-1.5 truncate">
                <span className="text-gray-500 w-5 text-xs">{r.rank}</span>
                <span className="truncate">{r.team_name}</span>
                {r.is_my_team && <span className="text-blue-400 text-xs">★</span>}
              </span>
              <span>{r.score.toFixed(1)}</span>
            </div>
          ))}
          <div className="pt-2 border-t border-gray-800 flex gap-4 text-xs text-gray-500">
            <span>Median {data.median_score}</span>
            <span>Mean {data.mean_score}</span>
          </div>
        </div>
      )}
    </Card>
  )
}
