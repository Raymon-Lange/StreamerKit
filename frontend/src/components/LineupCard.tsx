import { useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'
import { injuryColor, injuryLabel } from '../constants/injuryStatus'

interface RosterSlot {
  name: string
  mlb_team: string | null
  lineup_slot: string
  injury_status: string | null
  in_lineup: boolean | null
  lineup_status: string | null
  batting_slot: number | null
}

interface RosterData {
  team: string | null
  starters: RosterSlot[]
  bench: RosterSlot[]
}

function StatusBadge({ slot }: { slot: RosterSlot }) {
  if (slot.in_lineup === null) return null
  if (slot.in_lineup === true)
    return <span className="text-xs font-semibold text-green-400">▶ Starting</span>
  if (slot.lineup_status === 'lineup_not_posted')
    return <span className="text-xs font-semibold text-yellow-400">? Not Posted</span>
  if (slot.lineup_status === 'no_game')
    return <span className="text-xs font-semibold text-gray-500">— No Game</span>
  return <span className="text-xs font-semibold text-red-400">✕ Out</span>
}

function PlayerRow({ slot }: { slot: RosterSlot }) {
  return (
    <div className="py-2 flex items-start justify-between gap-2">
      <div className="flex flex-col gap-0.5 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="font-medium text-white text-sm truncate">{slot.name}</span>
          {slot.injury_status && injuryColor[slot.injury_status] && (
            <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium shrink-0 ${injuryColor[slot.injury_status]}`}>
              {injuryLabel[slot.injury_status]}
            </span>
          )}
        </div>
        <span className="text-xs text-gray-400">
          {slot.mlb_team ?? '—'} · {slot.lineup_slot}
        </span>
      </div>
      <div className="flex flex-col items-end gap-1 shrink-0">
        <StatusBadge slot={slot} />
        {slot.batting_slot != null && (
          <span className="text-xs text-gray-500">#{slot.batting_slot}</span>
        )}
      </div>
    </div>
  )
}

function SectionLabel({ label }: { label: string }) {
  return (
    <span className="text-xs font-semibold uppercase tracking-widest text-gray-600">{label}</span>
  )
}

export default function LineupCard() {
  const [data, setData] = useState<RosterData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  const fetchData = (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    api.myRoster()
      .then(d => {
        setData(d as RosterData)
        setError(null)
      })
      .catch(e => setError(String(e)))
      .finally(() => {
        setLoading(false)
        setRefreshing(false)
      })
  }

  useEffect(() => { fetchData() }, [])

  const title = data?.team ? `Lineup · ${data.team}` : 'My Lineup'

  return (
    <Card title={title} loading={loading} error={error}>
      <div className="flex justify-end -mt-1 mb-1">
        <button
          onClick={() => fetchData(true)}
          disabled={refreshing}
          className="text-xs text-gray-500 hover:text-gray-300 disabled:opacity-40 transition-colors"
        >
          {refreshing ? 'Refreshing…' : '↺ Refresh'}
        </button>
      </div>

      <div className="flex flex-col">
        <SectionLabel label="Starters" />
        <div className="flex flex-col divide-y divide-gray-800">
          {data?.starters.map(s => <PlayerRow key={s.name} slot={s} />)}
          {data?.starters.length === 0 && (
            <p className="text-gray-500 text-sm py-2">No starters.</p>
          )}
        </div>

        <div className="border-t border-gray-700 my-2" />
        <SectionLabel label="Bench" />
        <div className="flex flex-col divide-y divide-gray-800">
          {data?.bench.map(s => <PlayerRow key={s.name} slot={s} />)}
          {data?.bench.length === 0 && (
            <p className="text-gray-500 text-sm py-2">No bench players.</p>
          )}
        </div>
      </div>
    </Card>
  )
}
