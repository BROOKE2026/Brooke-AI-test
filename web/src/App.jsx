import { useState, useEffect, useRef, useCallback } from 'react'
import { chat, login, logout, health, getApiBase, setApiBase } from './api.js'

const DEMO_LOGINS = [
  { code: 'sarah-2026',  who: 'Sarah Whitfield',  note: 'client since 2019, 3 accounts' },
  { code: 'marcus-2026', who: 'Marcus Delaney',   note: 'client since 2022, 2 accounts' },
  { code: 'elena-2026',  who: 'Elena Vasquez',    note: 'client since 2015, 3 accounts' },
]

const STARTERS = [
  'What was my AGI last year?',
  'What are my account balances?',
  'What documents do I have?',
  'When is my next meeting?',
]

const TOOL_LABEL = {
  get_tax_return:      'Looking up your tax return',
  get_accounts:        'Pulling your account balances',
  get_holdings:        'Reading your holdings',
  get_documents:       'Checking your documents',
  get_meetings:        'Checking your calendar',
  escalate_to_advisor: 'Sending this to your advisor',
}

/* ------------------------------------------------------------------ shell */

export default function App() {
  const [session, setSession] = useState(() => {
    try { return JSON.parse(localStorage.getItem('brooke.session')) } catch { return null }
  })
  const [settingsOpen, setSettingsOpen] = useState(false)

  const save = (s) => {
    setSession(s)
    if (s) localStorage.setItem('brooke.session', JSON.stringify(s))
    else localStorage.removeItem('brooke.session')
  }

  return (
    <div className="app">
      <Header session={session} onSignOut={() => { logout(session?.token); save(null) }}
              onSettings={() => setSettingsOpen(true)} />
      {session
        ? <Chat session={session} onExpired={() => save(null)} />
        : <Login onSignedIn={save} onSettings={() => setSettingsOpen(true)} />}
      {settingsOpen && <Settings onClose={() => setSettingsOpen(false)} />}
    </div>
  )
}

function Header({ session, onSignOut, onSettings }) {
  return (
    <header className="header">
      <div className="brand">
        <div className="mark">B</div>
        <div>
          <div className="brand-name">BrookHaven</div>
          <div className="brand-sub">Client Portal</div>
        </div>
      </div>
      <div className="header-right">
        <StatusDot />
        <button className="icon-btn" onClick={onSettings} title="Connection settings">⚙</button>
        {session && (
          <>
            <span className="who">{session.name}</span>
            <button className="ghost-btn" onClick={onSignOut}>Sign out</button>
          </>
        )}
      </div>
    </header>
  )
}

function StatusDot() {
  const [state, setState] = useState('checking')
  const [detail, setDetail] = useState('')

  useEffect(() => {
    let alive = true
    const check = async () => {
      try {
        const h = await health()
        if (!alive) return
        const ok = h.ollama_up && h.model_present
        setState(ok ? 'up' : 'degraded')
        setDetail(ok ? `${h.model} ready`
          : h.ollama_up ? `${h.model} not pulled on host` : 'model host offline')
      } catch {
        if (!alive) return
        setState('down'); setDetail(`cannot reach ${getApiBase()}`)
      }
    }
    check()
    const t = setInterval(check, 20000)
    return () => { alive = false; clearInterval(t) }
  }, [])

  return <span className={`status status-${state}`} title={detail}>
    <i /> {state === 'up' ? 'Connected' : state === 'checking' ? 'Connecting' : state === 'degraded' ? 'Degraded' : 'Offline'}
  </span>
}

/* --------------------------------------------------------------- settings */

function Settings({ onClose }) {
  const [url, setUrl] = useState(getApiBase())
  const [msg, setMsg] = useState(null)
  const [busy, setBusy] = useState(false)

  const test = async () => {
    setBusy(true); setMsg(null)
    setApiBase(url)
    try {
      const h = await health()
      setMsg({ ok: true, text: `Connected. Model ${h.model}${h.model_present ? '' : ' (NOT pulled on host)'}.` })
    } catch (e) {
      setMsg({ ok: false, text: `Could not reach it. ${e.message}` })
    }
    setBusy(false)
  }

  return (
    <div className="modal-bg" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <h2>Connection</h2>
        <p className="muted">
          Where the Brooke server is running. Point this at your tunnel URL to reach
          the model host from anywhere.
        </p>
        <input className="input" value={url} onChange={e => setUrl(e.target.value)}
               placeholder="https://something.trycloudflare.com" spellCheck={false} />
        {msg && <div className={msg.ok ? 'note note-ok' : 'note note-bad'}>{msg.text}</div>}
        <div className="row">
          <button className="ghost-btn" onClick={onClose}>Close</button>
          <button className="btn" onClick={test} disabled={busy}>
            {busy ? 'Testing' : 'Save and test'}
          </button>
        </div>
      </div>
    </div>
  )
}

/* ------------------------------------------------------------------ login */

export function Login({ onSignedIn, onSettings }) {
  const [passcode, setPasscode] = useState('')
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e?.preventDefault()
    if (!passcode.trim()) return
    setBusy(true); setErr(null)
    try {
      const s = await login(passcode)
      onSignedIn(s)
    } catch (e) {
      setErr(e.message.includes('fetch') || e.message.includes('Failed')
        ? `Cannot reach the server at ${getApiBase()}. Check connection settings.`
        : e.message)
    }
    setBusy(false)
  }

  return (
    <main className="center">
      <div className="card">
        <h1>Sign in</h1>
        <p className="muted">Enter your client passcode to talk with Brooke.</p>
        <form onSubmit={submit}>
          <input className="input" type="password" value={passcode} autoFocus
                 placeholder="Passcode" spellCheck={false}
                 onChange={e => { setPasscode(e.target.value); setErr(null) }} />
          {err && <div className="note note-bad">{err}</div>}
          <button className="btn wide" disabled={busy || !passcode.trim()}>
            {busy ? 'Signing in' : 'Sign in'}
          </button>
        </form>

        <div className="demo-box">
          <div className="demo-title">Demo logins</div>
          {DEMO_LOGINS.map(d => (
            <button key={d.code} className="demo-row" onClick={() => setPasscode(d.code)}>
              <code>{d.code}</code>
              <span>{d.who}<em>{d.note}</em></span>
            </button>
          ))}
          <p className="tiny">
            All records are fictional. Each login sees only its own data, which is
            enforced on the server, not in the model.
          </p>
        </div>
        <button className="link-btn" onClick={onSettings}>Connection settings</button>
      </div>
    </main>
  )
}

/* ------------------------------------------------------------------- chat */

function Chat({ session, onExpired }) {
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

  const send = useCallback(async (text) => {
    const q = (text ?? draft).trim()
    if (!q || busy) return
    setDraft(''); setBusy(true); setActivity('Thinking')

    const history = messages.map(m => ({ role: m.role, content: m.content }))
    setMessages(m => [...m, { role: 'user', content: q },
                             { role: 'assistant', content: '', tools: [] }])

    abort.current = new AbortController()
    let failed = false

    await chat({
      token: session.token, message: q, history,
      signal: abort.current.signal,
      onEvent: (e) => {
        if (e.type === 'token') {
          setActivity(null)
          setMessages(m => {
            const c = [...m]; c[c.length - 1] = {
              ...c[c.length - 1], content: c[c.length - 1].content + e.text }
            return c
          })
        } else if (e.type === 'tool') {
          setActivity(TOOL_LABEL[e.name] || `Running ${e.name}`)
          setMessages(m => {
            const c = [...m]; const last = c[c.length - 1]
            c[c.length - 1] = { ...last, tools: [...(last.tools || []), e.name] }
            return c
          })
        } else if (e.type === 'status') {
          setActivity(e.text)
        } else if (e.type === 'expired') {
          failed = true; onExpired()
        } else if (e.type === 'error') {
          failed = true
          setMessages(m => {
            const c = [...m]; c[c.length - 1] = {
              ...c[c.length - 1], error: e.text }
            return c
          })
        }
      },
    }).catch(err => {
      if (err.name === 'AbortError') return
      failed = true
      setMessages(m => {
        const c = [...m]; c[c.length - 1] = {
          ...c[c.length - 1], error: `Connection lost. ${err.message}` }
        return c
      })
    })

    if (!failed) {
      setMessages(m => {
        const c = [...m]
        if (!c[c.length - 1].content) {
          c[c.length - 1] = { ...c[c.length - 1], error: 'No response from the model.' }
        }
        return c
      })
    }
    setBusy(false); setActivity(null)
  }, [draft, busy, messages, session, onExpired])

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <main className="chat">
      <div className="scroll" ref={scroller}>
        {messages.length === 0 && (
          <div className="welcome">
            <div className="avatar lg">B</div>
            <h2>Hello {session.name.split(' ')[0]}</h2>
            <p className="muted">
              I can look up your tax returns, accounts, holdings, documents and meetings.
              Anything that needs advice, I will pass to {session.advisor}.
            </p>
            <div className="starters">
              {STARTERS.map(s => (
                <button key={s} className="starter" onClick={() => send(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => {
          // While tools are running the assistant slot is still empty; the
          // activity indicator below stands in for it. Rendering both showed
          // two avatars stacked on top of each other.
          if (m.role === 'assistant' && !m.content && !m.error && !m.tools?.length) return null
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
            </div>
          </div>
        )})}

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
        <textarea
          className="composer-input" rows={1} value={draft} disabled={busy}
          placeholder={busy ? 'Brooke is responding' : `Ask Brooke about your accounts`}
          onChange={e => setDraft(e.target.value)} onKeyDown={onKey} />
        <button className="send" onClick={() => send()} disabled={busy || !draft.trim()}
                title="Send">↑</button>
      </div>
      <div className="disclaimer">
        Brooke provides information only and does not give investment advice.
        Demo environment with fictional records.
      </div>
    </main>
  )
}
