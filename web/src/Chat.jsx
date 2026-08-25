import { useState, useEffect, useRef, useCallback } from 'react'
import { chat, bookMeeting } from './api.js'

const TOOL_LABEL = {
  get_performance:       'Calculating your returns',
  get_allocation:        'Reading your asset mix',
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

export default function Chat({ session, onExpired, onNavigate, onClose, onRefreshData }) {
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
                             { role: 'assistant', content: '', tools: [], links: [], steps: null, schedule: null }])

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
        } else if (e.type === 'schedule') {
          patchLast(l => ({ ...l, schedule: { ...e, booked: null, busy: false } }))
        } else if (e.type === 'steps') {
          // Rendered verbatim from the server. Never model-generated, so the
          // instructions a client follows cannot be paraphrased or truncated.
          patchLast(l => ({ ...l, steps: { title: e.title, list: e.steps, note: e.note } }))
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

  const book = async (i, slot) => {
    setMessages(ms => {
      const c = [...ms]; const m = { ...c[i] }
      m.schedule = { ...m.schedule, busy: true }; c[i] = m; return c
    })
    try {
      const res = await bookMeeting(session.token, {
        topic: messages[i]?.schedule?.topic || '',
        advisor_type: messages[i]?.schedule?.advisor_type || 'advisor',
        date: slot?.date || '', time: slot?.time || '',
      })
      setMessages(ms => {
        const c = [...ms]; const m = { ...c[i] }
        m.schedule = { ...m.schedule, busy: false, booked: res }; c[i] = m; return c
      })
      onRefreshData?.()
    } catch (err) {
      setMessages(ms => {
        const c = [...ms]; const m = { ...c[i] }
        m.schedule = { ...m.schedule, busy: false, error: err.message }; c[i] = m; return c
      })
    }
  }

  const downloadIcs = (ics, name) => {
    const blob = new Blob([ics], { type: 'text/calendar' })
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob); a.download = name || 'brookhaven-call.ics'
    a.click(); URL.revokeObjectURL(a.href)
  }

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
              && !m.tools?.length && !m.links?.length && !m.steps && !m.schedule) return null
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
                {m.steps && (
                  <div className="steps">
                    {m.steps.title && <strong>{m.steps.title}</strong>}
                    <ol>{m.steps.list.map((st, k) => <li key={k}>{st}</li>)}</ol>
                    {m.steps.note && <p className="steps-note">{m.steps.note}</p>}
                  </div>
                )}
                {m.error && <div className="bubble bubble-err">{m.error}</div>}
                {m.schedule && !m.schedule.booked && (
                  <div className="sched">
                    <strong>Schedule a call with {m.schedule.who}</strong>
                    <div className="sched-slots">
                      {m.schedule.slots?.map((sl, k) => (
                        <button key={k} className="starter" disabled={m.schedule.busy}
                                onClick={() => book(i, sl)}>{sl.label}</button>
                      ))}
                      <button className="starter" disabled={m.schedule.busy}
                              onClick={() => book(i, null)}>Flexible, have the office call me</button>
                    </div>
                    {m.schedule.error && <div className="note note-bad">{m.schedule.error}</div>}
                  </div>
                )}
                {m.schedule?.booked && (
                  <div className="sched">
                    <strong>Request sent</strong>
                    <p className="sched-note">
                      {m.schedule.booked.meeting.type}
                      {m.schedule.booked.meeting.date !== 'TBD'
                        ? `, ${m.schedule.booked.meeting.date} at ${m.schedule.booked.meeting.time}`
                        : ', the office will call to find a time'}
                      . {m.schedule.booked.note}
                    </p>
                    {m.schedule.booked.ics && (
                      <button className="gobtn sm"
                              onClick={() => downloadIcs(m.schedule.booked.ics)}>
                        Add to my calendar (.ics)
                      </button>
                    )}
                  </div>
                )}
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
