import DailyBrief from './components/DailyBrief'
import StreamerCard from './components/StreamerCard'
import RecentDrops from './components/RecentDrops'
import Optimizer from './components/Optimizer'
import WeeklyScores from './components/WeeklyScores'
import Profile from './components/Profile'

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <span className="text-lg font-bold tracking-tight text-white">StreamerKit</span>
        <span className="text-xs text-gray-500">Fantasy Baseball</span>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-6 grid grid-cols-1 lg:grid-cols-2 gap-4">
        <DailyBrief />
        <StreamerCard />
        <StreamerCard tomorrow />
        <RecentDrops />
        <Optimizer />
        <WeeklyScores />
        <Profile />
      </main>
    </div>
  )
}
