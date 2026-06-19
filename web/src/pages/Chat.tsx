import { useRef, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Message from '../components/Message'
import ChatInput from '../components/ChatInput'
import ProjectSidebar from '../components/ProjectSidebar'
import { useChat } from '../hooks/useChat'
import { useProjects } from '../hooks/useProjects'

export default function Chat() {
  const navigate = useNavigate()
  const { messages, streaming, latencyMs, send, reset } = useChat()
  const projects = useProjects()
  const [activeContext, setActiveContext] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function handleSend(text: string) {
    send(text, activeContext)
  }

  return (
    <div className="h-screen bg-bg flex overflow-hidden">
      <ProjectSidebar
        projects={projects}
        activeContext={activeContext}
        onSelect={setActiveContext}
        onBack={() => navigate('/')}
      />

      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">
              {activeContext
                ? <span>Contexto: <span className="text-accent font-medium">{activeContext}</span></span>
                : 'Sem contexto ativo'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            {latencyMs !== null && (
              <span className="text-xs text-gray-600">{latencyMs}ms</span>
            )}
            <button
              onClick={reset}
              disabled={streaming}
              className="text-xs text-gray-600 hover:text-gray-400 transition-colors disabled:opacity-40"
            >
              Limpar
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-3">
          {messages.length === 0 && (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-gray-700 text-sm">
                {activeContext
                  ? `Contexto do projeto "${activeContext}" ativo. Faz a tua pergunta.`
                  : 'Olá! Em que posso ajudar?'}
              </p>
            </div>
          )}
          {messages.map((m, i) => (
            <Message key={i} role={m.role} content={m.content} streaming={m.streaming} />
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-4 py-3 border-t border-border shrink-0">
          <ChatInput onSend={handleSend} disabled={streaming} />
        </div>
      </div>
    </div>
  )
}
