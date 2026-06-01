interface CardProps {
  title: string
  children: React.ReactNode
  className?: string
  loading?: boolean
  error?: string | null
}

export default function Card({ title, children, className = '', loading, error }: CardProps) {
  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-xl p-5 flex flex-col gap-3 ${className}`}>
      <h2 className="text-xs font-semibold uppercase tracking-widest text-gray-500">{title}</h2>
      {loading && <p className="text-gray-500 text-sm">Loading…</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}
      {!loading && !error && children}
    </div>
  )
}
