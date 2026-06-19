interface MessageProps {
  role: 'user' | 'jarvis'
  content: string
  streaming?: boolean
}

export default function Message({ role, content, streaming }: MessageProps) {
  const isUser = role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? 'bg-surface-2 text-gray-200 rounded-br-sm'
            : 'bg-surface border border-border text-accent-2 rounded-bl-sm'
        }`}
      >
        {content}
        {streaming && (
          <span className="inline-block w-1.5 h-4 bg-accent ml-0.5 align-middle animate-pulse" />
        )}
      </div>
    </div>
  )
}
