import type { Project } from '../hooks/useProjects'

const STATUS_COLORS: Record<string, string> = {
  active:    'bg-green-900/40 text-green-400',
  exploring: 'bg-blue-900/40 text-blue-400',
  idea:      'bg-yellow-900/40 text-yellow-400',
  paused:    'bg-gray-800 text-gray-400',
  dead:      'bg-red-900/30 text-red-400',
}

interface ProjectSidebarProps {
  projects: Project[]
  activeContext: string | null
  onSelect: (name: string | null) => void
  onBack: () => void
}

export default function ProjectSidebar({ projects, activeContext, onSelect, onBack }: ProjectSidebarProps) {
  return (
    <aside className="w-64 shrink-0 bg-[#0f1117] border-r border-border flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <span className="text-accent font-bold tracking-widest text-sm">JARVIS</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-1">
        <p className="text-xs text-gray-600 uppercase tracking-wider px-1 mb-2">Projetos</p>

        {projects.length === 0 && (
          <p className="text-xs text-gray-600 px-2">Sem projetos. Usa o terminal para criar.</p>
        )}

        {projects.map(p => {
          const isActive = activeContext === p.name
          return (
            <button
              key={p.name}
              onClick={() => onSelect(isActive ? null : p.name)}
              className={`w-full text-left rounded-lg px-3 py-2.5 transition-colors ${
                isActive
                  ? 'bg-accent/15 border-l-2 border-accent'
                  : 'hover:bg-surface-2 border-l-2 border-transparent'
              }`}
            >
              <div className="text-sm font-medium text-gray-200 truncate">{p.name}</div>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${STATUS_COLORS[p.status] ?? STATUS_COLORS.paused}`}>
                  {p.status}
                </span>
                {p.goal && (
                  <span className="text-[10px] text-gray-600 truncate">{p.goal}</span>
                )}
              </div>
            </button>
          )
        })}
      </div>

      <div className="p-3 border-t border-border">
        <button
          onClick={onBack}
          className="text-xs text-gray-600 hover:text-gray-400 transition-colors"
        >
          ← Início
        </button>
      </div>
    </aside>
  )
}
