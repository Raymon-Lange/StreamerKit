import { useEffect, useState } from 'react'
import { api } from '../api'
import Card from './Card'
import { injuryColor, injuryLabel } from '../constants/injuryStatus'

interface RosterSlot {
  player_id: number
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

const SLOT_ORDER = ['C', '1B', '2B', 'SS', '3B', 'OF', 'DH', 'SP', 'RP']

function sortStarters(starters: RosterSlot[]): RosterSlot[] {
  return [...starters].sort((a, b) => {
    const aRank = SLOT_ORDER.indexOf(a.lineup_slot)
    const bRank = SLOT_ORDER.indexOf(b.lineup_slot)
    const aKey = aRank === -1 ? SLOT_ORDER.length : aRank
    const bKey = bRank === -1 ? SLOT_ORDER.length : bRank
    if (aKey !== bKey) return aKey - bKey
    return a.name.localeCompare(b.name)
  })
}

function StatusBadge({ slot }: { slot: RosterSlot }) {
  if (slot.in_lineup === null) return null
  if (slot.in_lineup === true)
    return (
      <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-green-900 text-green-300 text-xs font-bold shrink-0">
        {slot.batting_slot ?? '▶'}
      </span>
    )
  if (slot.lineup_status === 'lineup_not_posted')
    return <span className="text-xs font-semibold text-yellow-400">? Not Posted</span>
  if (slot.lineup_status === 'no_game')
    return <span className="text-xs font-semibold text-gray-500">— No Game</span>
  return <span className="text-xs font-semibold text-red-400">✕ Out</span>
}

function PlayerRow({
  slot,
  picked,
  onPick,
}: {
  slot: RosterSlot
  picked: boolean
  onPick: (slot: RosterSlot) => void
}) {
  return (
    <div
      className={`py-2 flex items-start justify-between gap-2 ${picked ? 'ring-1 ring-blue-500 rounded' : ''}`}
    >
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
      <div className="flex items-center gap-2 shrink-0">
        <div className="flex flex-col items-end gap-1">
          <StatusBadge slot={slot} />
          {slot.batting_slot != null && (
            <span className="text-xs text-gray-500">#{slot.batting_slot}</span>
          )}
        </div>
        <button
          onClick={() => onPick(slot)}
          title="Swap this player"
          className="text-gray-500 hover:text-gray-300 transition-colors text-sm"
        >
          ⇄
        </button>
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

  const [pickA, setPickA] = useState<RosterSlot | null>(null)
  const [pickB, setPickB] = useState<RosterSlot | null>(null)
  const [swapBusy, setSwapBusy] = useState(false)
  const [swapError, setSwapError] = useState<string | null>(null)
  const [swapMessage, setSwapMessage] = useState<string | null>(null)

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

  const handlePick = (slot: RosterSlot) => {
    setSwapError(null)
    if (!pickA) {
      setPickA(slot)
      return
    }
    if (pickA.player_id === slot.player_id) {
      setPickA(null)
      return
    }
    setPickB(slot)
  }

  const cancelSwap = () => {
    setPickA(null)
    setPickB(null)
    setSwapError(null)
  }

  const confirmSwap = () => {
    if (!pickA || !pickB) return
    setSwapBusy(true)
    setSwapError(null)
    api.swapLineup(pickA.player_id, pickB.player_id)
      .then(result => {
        setSwapMessage(result.message)
        setPickA(null)
        setPickB(null)
        fetchData(true)
        setTimeout(() => setSwapMessage(null), 4000)
      })
      .catch(e => setSwapError(String(e.message ?? e)))
      .finally(() => setSwapBusy(false))
  }

  const title = data?.team ? `Lineup · ${data.team}` : 'My Lineup'
  const isPicked = (slot: RosterSlot) =>
    pickA?.player_id === slot.player_id || pickB?.player_id === slot.player_id

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

      {pickA && !pickB && (
        <p className="text-xs text-blue-400 mb-1">
          Choose a player to swap with {pickA.name}… (tap ⇄ again to cancel)
        </p>
      )}

      {pickA && pickB && (
        <div className="bg-gray-800 rounded-lg p-3 mb-2 flex flex-col gap-2">
          <p className="text-sm text-gray-200">
            Swap {pickA.name} ({pickA.lineup_slot}) ⇄ {pickB.name} ({pickB.lineup_slot})?
          </p>
          {swapError && <p className="text-xs text-red-400">{swapError}</p>}
          <div className="flex gap-2">
            <button
              onClick={confirmSwap}
              disabled={swapBusy}
              className="text-xs px-2 py-1 rounded bg-green-700 hover:bg-green-600 disabled:opacity-40 text-white transition-colors"
            >
              {swapBusy ? 'Swapping…' : 'Confirm swap'}
            </button>
            <button
              onClick={cancelSwap}
              disabled={swapBusy}
              className="text-xs px-2 py-1 rounded bg-gray-700 hover:bg-gray-600 disabled:opacity-40 text-gray-200 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {swapMessage && <p className="text-xs text-green-400 mb-1">{swapMessage}</p>}

      <div className="flex flex-col">
        <SectionLabel label="Starters" />
        <div className="flex flex-col divide-y divide-gray-800">
          {data && sortStarters(data.starters).map(s => (
            <PlayerRow key={s.player_id} slot={s} picked={isPicked(s)} onPick={handlePick} />
          ))}
          {data?.starters.length === 0 && (
            <p className="text-gray-500 text-sm py-2">No starters.</p>
          )}
        </div>

        <div className="border-t border-gray-700 my-2" />
        <SectionLabel label="Bench" />
        <div className="flex flex-col divide-y divide-gray-800">
          {data?.bench.map(s => (
            <PlayerRow key={s.player_id} slot={s} picked={isPicked(s)} onPick={handlePick} />
          ))}
          {data?.bench.length === 0 && (
            <p className="text-gray-500 text-sm py-2">No bench players.</p>
          )}
        </div>
      </div>
    </Card>
  )
}
