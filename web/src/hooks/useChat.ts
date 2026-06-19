import { useState } from 'react'
import { BASE } from '../lib/api'

export interface Message {
  role: 'user' | 'jarvis'
  content: string
  streaming?: boolean
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [streaming, setStreaming] = useState(false)
  const [latencyMs, setLatencyMs] = useState<number | null>(null)

  async function send(text: string, contextProject?: string | null) {
    if (streaming || !text.trim()) return

    setMessages(prev => [...prev, { role: 'user', content: text }])
    setStreaming(true)
    setMessages(prev => [...prev, { role: 'jarvis', content: '', streaming: true }])

    try {
      const res = await fetch(`${BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, context_project: contextProject ?? null }),
      })

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buf = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buf += decoder.decode(value, { stream: true })

        const lines = buf.split('\n')
        buf = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = JSON.parse(line.slice(6))

          if (data.token) {
            setMessages(prev => {
              const next = [...prev]
              const last = { ...next[next.length - 1] }
              last.content += data.token
              next[next.length - 1] = last
              return next
            })
          }

          if (data.done) {
            setLatencyMs(data.latency_ms ?? null)
            setMessages(prev => {
              const next = [...prev]
              next[next.length - 1] = { ...next[next.length - 1], streaming: false }
              return next
            })
            setStreaming(false)
          }
        }
      }
    } catch {
      setMessages(prev => {
        const next = [...prev]
        next[next.length - 1] = { role: 'jarvis', content: '[Erro de ligação ao servidor]', streaming: false }
        return next
      })
      setStreaming(false)
    }
  }

  async function reset() {
    await fetch(`${BASE}/api/chat/history`, { method: 'DELETE' })
    setMessages([])
    setLatencyMs(null)
  }

  return { messages, streaming, latencyMs, send, reset }
}
