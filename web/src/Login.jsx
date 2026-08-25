import { useState } from 'react'
import { login, getApiBase } from './api.js'

const DEMO_LOGINS = [
  { code: 'sarah-2026',  who: 'Sarah Whitfield', note: 'client since 2019, 3 accounts' },
  { code: 'marcus-2026', who: 'Marcus Delaney',  note: 'client since 2022, 2 accounts' },
  { code: 'elena-2026',  who: 'Elena Vasquez',   note: 'client since 2015, 3 accounts' },
]

export default function Login({ onSignedIn, onSettings }) {
  const [passcode, setPasscode] = useState('')
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e?.preventDefault()
    if (!passcode.trim()) return
    setBusy(true); setErr(null)
    try {
      onSignedIn(await login(passcode))
    } catch (e) {
      setErr(/fetch|Failed|NetworkError/.test(e.message)
        ? `Cannot reach the server at ${getApiBase()}. Check connection settings.`
        : e.message)
    }
    setBusy(false)
  }

  return (
    <main className="center">
      <div className="card">
        <h1>Sign in</h1>
        <p className="muted">Enter your client passcode to open your portal.</p>
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
        <button className="link-btn" onClick={onSettings}>
          Connection settings ({getApiBase().replace(/^https?:\/\//, '')})
        </button>
      </div>
    </main>
  )
}
