import { useState, useEffect, useRef, useCallback } from 'react'
import { chat } from './api.js'

const TOOL_LABEL = {
  get_tax_return:        'Looking up your tax return',
  get_accounts:          'Pulling your account balances',
  get_holdings:          'Reading your holdings',
  get_documents:         'Checking your documents',
  get_meetings:          'Checking your calendar',
  get_activity:          'Reading recent activity',
  get_beneficiaries:     'Checking your beneficiaries',
  get_contribution_room: 'Checking your contribution room',
  get_fees:              'Looking up your fee schedule',
  get_howto:             'Finding the instructions',
  navigate_to:           'Finding that section',
  escalate_to_advisor:   'Sending this to your advisor',
}

const STARTERS = [
  'What was my AGI last year?',
  'How do I change my beneficiaries?',
  'How much more can I put in my Roth?',
  'Where do I download my statement?',
]

export default function Chat({ session, onExpired, onNavigate, onClose }) {
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [activity, setActivity] = useState(null)
  const scroller = useRef(null)
  const abort = useRef(null)

  useEffect(() => {
    const el = scroller.current
    if (el) el.scrollTop = el.scrollHeight
  }, [messages, activity])

  const patchLast = (fn) => setMessages(m => {
    const c = [...m]; c[c.length - 1] = fn(c[c.length - 1]); return c
  })

  const send = useCallback(async (text) => {
    const q = (text ?? draft).trim()
    if (!q || busy) return
    setDraft(''); setBusy(true); setActivity('Thinking')

    const history = messages.map(m => ({ role: m.role, content: m.content }))
    setMessages(m => [...m, { role: 'user', content: q },
                             { role: 'assistant', content: '', tools: [], links: [] }])

    abort.current = new AbortController()
    let failed = false

    await chat({
      token: session.token, message: q, history, signal: abort.current.signal,
      onEvent: (e) => {
        if (e.type === 'token') {
          setActivity(null)
          patchLast(l => ({ ...l, content: l.content + e.text }))
        } else if (e.type === 'tool') {
          setActivity(TOOL_LABEL[e.name] || `Running ${e.name}`)
          patchLast(l => ({ ...l, tools: [...l.tools, e.name] }))
        } else if (e.type === 'link') {
          // Destination comes from the server, never from the model's prose.
          patchLast(l => ({ ...l, links: [...l.links, { label: e.label, tab: e.tab, item: e.item }] }))
        } else if (e.type === 'status') {
          setActivity(e.text)
        } else if (e.type === 'expired') {
          failed = true; onExpired()
        } else if (e.type === 'error') {
          failed = true; patchLast(l => ({ ...l, error: e.text }))
        }
      },
    }).catch(err => {
      if (err.name === 'AbortError') return
      failed = true
      patchLast(l => ({ ...l, error: `Connection lost. ${err.message}` }))
    })

    if (!failed) patchLast(l => l.content ? l : { ...l, error: 'No response from the model.' })
    setBusy(false); setActivity(null)
  }, [draft, busy, messages, session, onExpired])

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <aside className="chatpanel">
      <div className="chathead">
        <div className="chathead-l"><div className="avatar sm">B</div><strong>Brooke</strong></div>
        <button className="icon-btn" onClick={onClose} title="Close Brooke">✕</button>
      </div>

      <div className="scroll" ref={scroller}>
        {messages.length === 0 && (
          <div className="welcome">
            <p className="muted">
              Ask about your accounts, or how to do something in the portal. Anything
              needing advice goes to {session.advisor}.
            </p>
            <div className="starters">
              {STARTERS.map(s => (
                <button key={s} className="starter" onClick={() => send(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => {
          if (m.role === 'assistant' && !m.content && !m.error
              && !m.tools?.length && !m.links?.length) return null
          return (
            <div key={i} className={`msg msg-${m.role}`}>
              {m.role === 'assistant' && <div className="avatar">B</div>}
              <div className="bubble-wrap">
                {m.tools?.length > 0 && (
                  <div className="tools">
                    {m.tools.map((t, j) => (
                      <span key={j} className="tool-chip">✓ {TOOL_LABEL[t] || t}</span>
                    ))}
                  </div>
                )}
                {m.content && <div className="bubble">{m.content}</div>}
                {m.error && <div className="bubble bubble-err">{m.error}</div>}
                {m.links?.map((l, j) => (
                  <button key={j} className="gobtn" onClick={() => onNavigate(l.tab, l.item)}>
                    {l.label} <span className="arrow">→</span>
                  </button>
                ))}
              </div>
            </div>
          )
        })}

        {activity && (
          <div className="msg msg-assistant">
            <div className="avatar">B</div>
            <div className="bubble bubble-activity">
              <span className="dots"><i /><i /><i /></span>{activity}
            </div>
          </div>
        )}
      </div>

      <div className="composer">
        <textarea className="composer-input" rows={1} value={draft} disabled={busy}
          placeholder={busy ? 'Brooke is responding' : 'Ask Brooke'}
          onChange={e => setDraft(e.target.value)} onKeyDown={onKey} />
        <button className="send" onClick={() => send()} disabled={busy || !draft.trim()}>↑</button>
      </div>
      <div className="disclaimer">Information only, not investment advice. Fictional demo records.</div>
    </aside>
  )
}
