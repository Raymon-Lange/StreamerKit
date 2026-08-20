/// <reference types="vite/client" />
const API_KEY = import.meta.env.VITE_API_KEY as string | undefined

async function apiFetch(path: string): Promise<unknown> {
  const res = await fetch(path, {
    headers: API_KEY ? { 'X-API-Key': API_KEY } : {},
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

async function apiPost(path: string, body: unknown): Promise<unknown> {
  const res = await fetch(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`
    try {
      const data = await res.json()
      if (data?.detail) detail = data.detail
    } catch {
      // response body wasn't JSON
    }
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  dashboard: () => apiFetch('/api/dashboard'),
  streamers: (tomorrow = false) =>
    apiFetch(`/api/streamers?tomorrow=${tomorrow}`),
  drops: (days = 2, top = 10) =>
    apiFetch(`/api/recent-drops?days=${days}&top=${top}`),
  pitcherStarts: (tomorrow = false) =>
    apiFetch(`/api/pitcher-starts?tomorrow=${tomorrow}`),
  weeklyScores: () => apiFetch('/api/weekly-scores?latest_scored=true'),
  optimizer: () => apiFetch('/api/roster-optimizer'),
  feedStatus: () => apiFetch('/api/feed-status'),
  myRoster: () => apiFetch('/api/my-roster'),
  swapLineup: (playerAId: number, playerBId: number) =>
    apiPost('/api/my-roster/swap', { player_a_id: playerAId, player_b_id: playerBId }) as Promise<{
      success: boolean
      message: string
    }>,
}
