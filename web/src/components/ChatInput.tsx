import { useState } from 'react'
import type { KeyboardEvent } from 'react'

interface ChatInputProps {
  onSend: (text: string) => void
  disabled: boolean
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState('')

  function submit() {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setValue('')
  }

  function onKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="flex items-end gap-2 bg-surface border border-border rounded-2xl px-3 py-2">
      <textarea
        className="flex-1 bg-transparent text-sm text-gray-200 placeholder-gray-600 resize-none focus:outline-none max-h-32"
        rows={1}
        placeholder="Escreve uma mensagem..."
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={onKey}
        disabled={disabled}
      />
      <button
        className="text-gray-500 hover:text-accent transition-colors p-1"
        aria-label="Voz (em breve)"
        disabled
      >
        🎤
      </button>
      <button
        onClick={submit}
        disabled={disabled || !value.trim()}
        className="bg-accent text-white text-sm px-3 py-1.5 rounded-xl disabled:opacity-40 hover:bg-accent/80 transition-colors"
      >
        ↑
      </button>
    </div>
  )
}
