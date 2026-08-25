import { useState, useEffect, useCallback } from 'react'
import { logout, health, getPortal, getApiBase, setApiBase, clearApiOverride, autoSelectBase, CANDIDATES } from './api.js'
import Login from './Login.jsx'
import Chat from './Chat.jsx'
import Portal from './Portal.jsx'

const TAB_ORDER = ['overview', 'accounts', 'documents', 'tax', 'meetings', 'forms']
const TAB_NAME = { overview: 'Overview', accounts: 'Accounts', documents: 'Documents',
                   tax: 'Tax', meetings: 'Meetings', forms: 'Forms' }

export default function App() {
  const [session, setSession] = useState(() => {
    try { return JSON.parse(localStorage.getItem('brooke.session')) } catch { return null }
  })
  const [data, setData] = useState(null)
  const [tab, setTab] = useState('overview')
  const [focus, setFocus] = useState(null)
  const [chatOpen, setChatOpen] = useState(true)
  const [settingsOpen, setSettingsOpen] = useState(false)
  const [loadErr, setLoadErr] = useState(null)
  const [probing, setProbing] = useState(true)
  const [probeAt, setProbeAt] = useState(null)

  // Find a reachable endpoint before anything tries to call one.
  useEffect(() => {
    let alive = true
    autoSelectBase(b => alive && setProbeAt(b))
      .finally(() => alive && setProbing(false))
    return () => { alive = false }
  }, [])

  const save = (s) => {
    setSession(s)
    if (s) localStorage.setItem('brooke.session', JSON.stringify(s))
    else { localStorage.removeItem('brooke.session'); setData(null) }
  }

  useEffect(() => {
    if (!session) return
    let alive = true
    getPortal(session.token)
      .then(d => alive && setData(d))
      .catch(e => { if (!alive) return; e.expired ? save(null) : setLoadErr(e.message) })
    return () => { alive = false }
  }, [session])

  // Brooke's buttons land here. The tab and item came from the server, so this
  // can never be pointed at a section that does not exist.
  const navigate = useCallback((t, item) => {
    if (t && TAB_NAME[t]) setTab(t)
    setFocus(item || null)
    if (window.innerWidth < 900) setChatOpen(false)
  }, [])

  if (probing) {
    return (
      <div className="app">
        <Header onSettings={() => setSettingsOpen(true)} />
        <main className="center">
          <div className="card" style={{ textAlign: 'center' }}>
            <p className="muted">Finding the server</p>
            {probeAt && <p className="tiny">trying {probeAt.replace(/^https?:\/\//, '')}</p>}
          </div>
        </main>
      </div>
    )
  }

  if (!session) {
    return (
      <div className="app">
        <Header onSettings={() => setSettingsOpen(true)} />
        <Login onSignedIn={save} onSettings={() => setSettingsOpen(true)} />
        {settingsOpen && <Settings onClose={() => setSettingsOpen(false)} />}
      </div>
    )
  }

  return (
    <div className="app app-wide">
      <Header session={session} onSettings={() => setSettingsOpen(true)}
              onSignOut={() => { logout(session.token); save(null) }} />
      <nav className="tabbar">
        {TAB_ORDER.map(t => (
          <button key={t} className={`tab ${t === tab ? 'on' : ''}`}
                  onClick={() => { setTab(t); setFocus(null) }}>{TAB_NAME[t]}</button>
        ))}
        {!chatOpen && (
          <button className="tab askbtn" onClick={() => setChatOpen(true)}>Ask Brooke</button>
        )}
      </nav>

      <div className="body">
        <main className="main">
          {loadErr
            ? <div className="note note-bad">{loadErr}</div>
            : <Portal data={data} tab={tab} focus={focus} onNavigate={navigate} />}
        </main>
        {chatOpen && (
          <Chat session={session} onExpired={() => save(null)}
                onNavigate={navigate} onClose={() => setChatOpen(false)}
                onRefreshData={() => getPortal(session.token).then(setData).catch(() => {})} />
        )}
      </div>
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
        {session && <>
          <span className="who">{session.name}</span>
          <button className="ghost-btn" onClick={onSignOut}>Sign out</button>
        </>}
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
  const label = { up: 'Connected', checking: 'Connecting', degraded: 'Degraded', down: 'Offline' }[state]
  return <span className={`status status-${state}`} title={detail}><i /> {label}</span>
}

function Settings({ onClose }) {
  const [url, setUrl] = useState(getApiBase())
  const [msg, setMsg] = useState(null)
  const [busy, setBusy] = useState(false)
  const test = async () => {
    setBusy(true); setMsg(null); setApiBase(url)
    try {
      const h = await health()
      setMsg({ ok: true, text: `Connected. Model ${h.model}${h.model_present ? '' : ' (NOT pulled on host)'}.` })
    } catch (e) { setMsg({ ok: false, text: `Could not reach it. ${e.message}` }) }
    setBusy(false)
  }
  return (
    <div className="modal-bg" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <h2>Connection</h2>
        <p className="muted">Where the Brooke server is running. Point this at your tunnel URL to reach the model host from anywhere.</p>
        <input className="input" value={url} onChange={e => setUrl(e.target.value)}
               placeholder="https://something.trycloudflare.com" spellCheck={false} />
        {msg && <div className={msg.ok ? 'note note-ok' : 'note note-bad'}>{msg.text}</div>}
        <div className="demo-box" style={{ marginTop: 14 }}>
          <div className="demo-title">Known endpoints</div>
          {CANDIDATES.map(c => (
            <button key={c} className="demo-row" onClick={() => setUrl(c)}>
              <span><code style={{ fontSize: 11 }}>{c.replace(/^https?:\/\//, '')}</code></span>
            </button>
          ))}
        </div>
        <div className="row">
          <button className="ghost-btn" onClick={() => { clearApiOverride(); location.reload() }}>
            Use automatic
          </button>
          <button className="ghost-btn" onClick={onClose}>Close</button>
          <button className="btn" onClick={test} disabled={busy}>{busy ? 'Testing' : 'Save and test'}</button>
        </div>
      </div>
    </div>
  )
}
