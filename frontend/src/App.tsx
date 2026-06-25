import { useState } from 'react'
import DailyBrief from './components/DailyBrief'
import LineupCard from './components/LineupCard'
import FeedSourcesCard from './components/FeedSourcesCard'
import Optimizer from './components/Optimizer'
import Profile from './components/Profile'
import RecentDrops from './components/RecentDrops'
import ResponseCacheCard from './components/ResponseCacheCard'
import StreamerCard from './components/StreamerCard'
import WeeklyScores from './components/WeeklyScores'

type Tab = 'dashboard' | 'feed-status'

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard')

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <span className="text-lg font-bold tracking-tight text-white">StreamerKit</span>
        <nav className="flex items-center gap-1">
          <button
            onClick={() => setTab('dashboard')}
            className={`text-xs px-3 py-1.5 rounded transition-colors ${
              tab === 'dashboard'
                ? 'bg-gray-800 text-white'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setTab('feed-status')}
            className={`text-xs px-3 py-1.5 rounded transition-colors ${
              tab === 'feed-status'
                ? 'bg-gray-800 text-white'
                : 'text-gray-500 hover:text-gray-300'
            }`}
          >
            Feed Status
          </button>
        </nav>
        <span className="text-xs text-gray-500">Fantasy Baseball</span>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6">
        {tab === 'dashboard' ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <DailyBrief />
            <StreamerCard />
            <StreamerCard tomorrow />
            <RecentDrops />
            <Optimizer />
            <WeeklyScores />
            <LineupCard />
            <Profile />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <FeedSourcesCard />
            <ResponseCacheCard />
          </div>
        )}
      </main>
    </div>
  )
}
