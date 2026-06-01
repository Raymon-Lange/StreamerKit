import { useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'

interface Swap {
  start: { name: string; mlb_team: string; action: string; reason: string; trend_label: string }
  sit: { name: string; mlb_team: string; action: string; trend_label: string }
  slot: string
  score_gap: number
}

interface OptimizerData {
  team: string | null
  swap_count: number
  swaps: Swap[]
}

export default function Optimizer() {
  const [data, setData] = useState<OptimizerData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.optimizer()
      .then(d => setData(d as OptimizerData))
      .catch(e => setError(String(e)))
      .finally(() => setLoading(false))
  }, [])

  return (
    <Card title="Roster Optimizer" loading={loading} error={error}>
      {data && (
        <>
          {data.swap_count === 0 ? (
            <p className="text-green-400 text-sm">✓ Lineup looks optimal — no swaps needed.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {data.swaps.map((s, i) => (
                <div key={i} className="bg-gray-800 rounded-lg p-3 flex flex-col gap-1">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">{s.slot} · gap {s.score_gap}</span>
                  </div>
                  <div className="flex gap-2 items-baseline">
                    <span className="text-green-400 text-xs font-semibold w-10">START</span>
                    <span className="text-white text-sm font-medium">{s.start.name}</span>
                    <span className="text-gray-400 text-xs">{s.start.mlb_team} · {s.start.trend_label}</span>
                  </div>
                  <p className="text-xs text-gray-400 pl-12">{s.start.reason}</p>
                  <div className="flex gap-2 items-baseline">
                    <span className="text-red-400 text-xs font-semibold w-10">SIT</span>
                    <span className="text-gray-300 text-sm">{s.sit.name}</span>
                    <span className="text-gray-500 text-xs">{s.sit.mlb_team} · {s.sit.trend_label}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </Card>
  )
}
