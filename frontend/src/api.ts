/// <reference types="vite/client" />
const API_KEY = import.meta.env.VITE_API_KEY as string | undefined

async function apiFetch(path: string): Promise<unknown> {
  const res = await fetch(path, {
    headers: API_KEY ? { 'X-API-Key': API_KEY } : {},
  })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
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
}
