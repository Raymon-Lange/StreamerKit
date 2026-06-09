import { useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'
import { injuryColor, injuryLabel } from '../constants/injuryStatus'

interface DropRow {
  name: string
  mlb_team: string
  kind: 'H' | 'P'
  dropped_by: string
  injury_status: string | null
  recommendation: { action: string; reason: string; score: number }
}

const actionColor: Record<string, string> = {
  'MUST ADD': 'text-green-400',
  'WIN-NOW ADD': 'text-green-300',
  'CONSIDER': 'text-yellow-400',
  'PICKUP': 'text-blue-400',
}

export default function RecentDrops() {
  const [rows, setRows] = useState<DropRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.drops(2, 8)
      .then(d => setRows(((d as { rows: DropRow[] }).rows ?? []).slice(0, 8)))
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Card title="Recent Drops" loading={loading} error={error}>
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
              <span className="text-xs text-gray-400">{r.mlb_team} · dropped by {r.dropped_by}</span>
              <span className="text-xs text-gray-500 truncate">{r.recommendation.reason}</span>
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              <span className={`text-xs font-semibold ${actionColor[r.recommendation.action] ?? 'text-gray-400'}`}>
                {r.recommendation.action}
              </span>
              <span className="text-xs text-gray-500">{r.kind === 'H' ? 'Hitter' : 'Pitcher'}</span>
            </div>
          </div>
        ))}
        {rows.length === 0 && <p className="text-gray-500 text-sm">No notable drops.</p>}
      </div>
    </Card>
  )
}
