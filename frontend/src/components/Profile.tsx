import { useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'

interface ProfileData {
  league: string
  team: string | null
  period: number
  generated_on: string
}

export default function Profile() {
  const [data, setData] = useState<ProfileData | null>(null)

  useEffect(() => {
    api.weeklyScores()
      .then(d => {
        const scores = d as { league: string; period: number; generated_on: string; my_team?: { team_name: string } | null }
        setData({
          league: scores.league,
          team: scores.my_team?.team_name ?? null,
          period: scores.period,
          generated_on: scores.generated_on,
        })
      })
      .catch(() => null)
  }, [])

  return (
    <Card title="Profile" className="col-span-1 lg:col-span-2">
      <div className="flex flex-wrap gap-6 text-sm">
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">League</span>
          <span className="text-white">{data?.league ?? '—'}</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">Team</span>
          <span className="text-white">{data?.team ?? '—'}</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">Current Week</span>
          <span className="text-white">{data?.period != null ? `Week ${data.period}` : '—'}</span>
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-xs text-gray-500">Last Refreshed</span>
          <span className="text-white">{data?.generated_on ?? '—'}</span>
        </div>
      </div>
    </Card>
  )
}
