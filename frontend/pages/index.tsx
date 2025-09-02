"use client";
import { useMemo, useState } from 'react'

interface Message { role: 'user' | 'assistant'; content: string }
interface Preferences {
  tone?: string
  format?: string
  language?: string
  interaction?: string
  topics?: string | string[]
}

const REQUIRED_KEYS: (keyof Preferences)[] = ['tone', 'format', 'language', 'interaction', 'topics']

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I\'m your Latest News Agent. To tailor updates, may I ask: Preferred Tone of Voice?' }
  ])
  const [input, setInput] = useState('')
  const [prefs, setPrefs] = useState<Preferences>({})
  const [loading, setLoading] = useState(false)

  const checklist = useMemo(() => REQUIRED_KEYS.map((k) => ({ key: k, done: !!(prefs as any)[k] })), [prefs])

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:12001'

  async function sendMessage(text: string) {
    // capture possible local prefs change synchronously
    const colon = text.indexOf(':')
    let outgoingPrefs = { ...prefs }
    if (colon > 0) {
      const key = text.slice(0, colon).trim().toLowerCase()
      const value = text.slice(colon + 1).trim()
      if (['tone', 'format', 'language', 'interaction', 'topics'].includes(key)) {
        outgoingPrefs = { ...outgoingPrefs, [key]: key === 'topics' ? value.split(',').map(s => s.trim()) : value }
        setPrefs(outgoingPrefs)
      }
    }

    const nextMessages: Message[] = [...messages, { role: 'user' as const, content: text }];
    setMessages(nextMessages)
    setLoading(true)
    try {
      const res = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: nextMessages, preferences: outgoingPrefs }),
      })
      const data = await res.json()
      setMessages(data.messages)
      setPrefs(data.updatedPreferences)
    } catch (e) {
      setMessages((m) => [...m, { role: 'assistant', content: 'Error contacting backend.' }])
    } finally {
      setLoading(false)
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!input.trim()) return
    sendMessage(input)
    setInput('')
  }

  return (
    <div className="container">
      <div className="header">
        <h2>Latest News Agent</h2>
        <span className="tag">demo</span>
      </div>

      <div className="grid">
        <div className="panel chat">
          <div className="messages">
            {messages.map((m, i) => (
              <div className={`msg ${m.role === 'user' ? 'you' : ''}`} key={i}>
                <div className={`bubble ${m.role === 'user' ? 'user' : 'assistant'}`}>
                  <b>{m.role === 'user' ? 'You' : 'Agent'}: </b>
                  <span>{m.content}</span>
                </div>
              </div>
            ))}
          </div>
          <form onSubmit={onSubmit} className="inputBar">
            <input
              className="textInput"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your message... (tip: tone: formal, topics: technology, ai)"
            />
            <button className="button" type="submit" disabled={loading}>
              {loading ? 'Sending…' : 'Send'}
            </button>
          </form>
        </div>

        <aside className="panel sidebar">
          <h4>Preferences Checklist</h4>
          <ul className="checklist">
            {checklist.map((c) => (
              <li key={c.key}>
                <input type="checkbox" checked={c.done} readOnly /> {c.key}
              </li>
            ))}
          </ul>
          <div className="hint">
            You can set preferences by typing commands like: <code>tone: formal</code>, <code>format: bullet points</code>, <code>language: English</code>, <code>interaction: concise</code>, <code>topics: technology, ai</code>.
          </div>
        </aside>
      </div>
    </div>
  )
}
