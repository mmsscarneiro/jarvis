interface OrbProps { onClick: () => void }

export default function Orb({ onClick }: OrbProps) {
  return (
    <div className="flex flex-col items-center gap-5">
      <button
        onClick={onClick}
        className="w-28 h-28 rounded-full focus:outline-none animate-orb-pulse"
        style={{
          background: 'radial-gradient(circle at 35% 35%, #818cf8, #4f46e5, #1e1b4b)',
          boxShadow: '0 0 40px #4f46e580, 0 0 80px #4f46e530',
        }}
        aria-label="Abrir chat"
      />
      <div className="flex gap-3">
        <button
          onClick={onClick}
          className="px-5 py-2 rounded-full bg-surface border border-border text-accent-2 text-sm hover:bg-accent/10 transition-colors"
        >
          🎤 Falar
        </button>
        <button
          onClick={onClick}
          className="px-5 py-2 rounded-full bg-surface border border-border text-accent-2 text-sm hover:bg-accent/10 transition-colors"
        >
          ✏️ Escrever
        </button>
      </div>
    </div>
  )
}
