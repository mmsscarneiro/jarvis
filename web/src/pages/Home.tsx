import { useNavigate } from 'react-router-dom'
import Orb from '../components/Orb'
import StatusCard from '../components/StatusCard'
import { useStatus } from '../hooks/useStatus'
import { useProjects } from '../hooks/useProjects'

export default function Home() {
  const navigate = useNavigate()
  const status = useStatus()
  const projects = useProjects()
  const activeCount = projects.filter(p => p.status === 'active').length

  return (
    <div className="min-h-screen bg-bg flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-border">
        <span className="text-accent font-bold tracking-widest text-sm">JARVIS</span>
        {status ? (
          <span className={`text-xs px-3 py-1 rounded-full font-medium ${
            status.ollama_ok
              ? 'bg-green-900/40 text-green-400'
              : 'bg-red-900/40 text-red-400'
          }`}>
            {status.ollama_ok ? '● Ollama online' : '● Ollama offline'}
          </span>
        ) : (
          <span className="text-xs text-gray-600">A verificar...</span>
        )}
      </header>

      {/* Status cards */}
      <div className="grid grid-cols-3 gap-4 px-6 pt-8 max-w-2xl mx-auto w-full">
        <StatusCard
          label="Modelo"
          value={status?.model ?? '—'}
          sub="RTX 3060"
        />
        <StatusCard
          label="Projetos"
          value={String(projects.length)}
          sub={`${activeCount} ativo${activeCount !== 1 ? 's' : ''}`}
          highlight={activeCount > 0 ? 'green' : 'none'}
        />
        <StatusCard
          label="Latência"
          value={status?.last_latency_ms ? `${status.last_latency_ms}ms` : '—'}
          sub="última resposta"
        />
      </div>

      {/* Orb */}
      <div className="flex-1 flex items-center justify-center py-12">
        <Orb onClick={() => navigate('/chat')} />
      </div>
    </div>
  )
}
