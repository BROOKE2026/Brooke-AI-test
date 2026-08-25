// Talks to the Brooke API. The base URL is stored in localStorage so the
// published site never needs rebuilding when the tunnel URL changes.

const KEY  = 'brooke.apiBase'      // manual override, wins over everything
const AUTO = 'brooke.apiAuto'      // whichever candidate answered this session

// The API is reachable by more than one route, and which one works depends on
// where the viewer is. A tailnet member resolves the Tailscale name to an
// internal address; everyone else takes the public ingress. Rather than pick
// one and hope, probe them and use whichever actually answers.
export const CANDIDATES = [
  import.meta.env.VITE_API_BASE,
  'https://wayne-heater-britain-detected.trycloudflare.com',
  'https://servers-mac-mini.tail64e16c.ts.net',
  'http://localhost:8080',
].filter(Boolean).filter((v, i, a) => a.indexOf(v) === i)

export function getApiBase() {
  return localStorage.getItem(KEY)
      || sessionStorage.getItem(AUTO)
      || CANDIDATES[0]
}

/** Probe each candidate and remember the first that responds. */
export async function autoSelectBase(onProgress) {
  if (localStorage.getItem(KEY)) return getApiBase()   // user chose, respect it
  const cached = sessionStorage.getItem(AUTO)
  if (cached) return cached
  for (const base of CANDIDATES) {
    onProgress?.(base)
    try {
      const ctrl = new AbortController()
      const timer = setTimeout(() => ctrl.abort(), 5000)
      const r = await fetch(`${base}/api/health`, { signal: ctrl.signal })
      clearTimeout(timer)
      if (r.ok) { sessionStorage.setItem(AUTO, base); return base }
    } catch { /* try the next one */ }
  }
  return CANDIDATES[0]
}
export function setApiBase(url) {
  localStorage.setItem(KEY, url.replace(/\/+$/, ''))
  sessionStorage.removeItem(AUTO)
}

export function clearApiOverride() {
  localStorage.removeItem(KEY)
  sessionStorage.removeItem(AUTO)
}

export async function health() {
  const r = await fetch(`${getApiBase()}/api/health`)
  if (!r.ok) throw new Error(`Health check returned ${r.status}`)
  return r.json()
}

export async function login(passcode) {
  const r = await fetch(`${getApiBase()}/api/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ passcode }),
  })
  if (!r.ok) {
    // Say exactly what failed and where. "Not found" with no context sent us
    // chasing the wrong problem for a while.
    const body = await r.json().catch(() => null)
    const detail = body && body.detail
    if (r.status === 401) throw new Error(detail || 'That passcode was not recognised')
    if (r.status === 404) throw new Error(
      `The server at ${getApiBase()} has no /api/login. That address is probably ` +
      `the website rather than the API. Fix it in Connection settings.`)
    throw new Error(`${getApiBase()} returned HTTP ${r.status}${detail ? ': ' + detail : ''}`)
  }
  return r.json()
}

export async function getPortal(token) {
  const r = await fetch(`${getApiBase()}/api/portal`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (r.status === 401) { const e = new Error('expired'); e.expired = true; throw e }
  if (!r.ok) throw new Error(`Portal load failed (${r.status})`)
  return r.json()
}

export async function bookMeeting(token, payload) {
  const r = await fetch(`${getApiBase()}/api/meeting_request`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify(payload),
  })
  if (!r.ok) throw new Error(`Request failed (${r.status})`)
  return r.json()
}

export async function logout(token) {
  try {
    await fetch(`${getApiBase()}/api/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    })
  } catch { /* best effort */ }
}

/**
 * Stream a chat turn. Calls onEvent for each server-sent event:
 *   {type:'token'|'tool'|'status'|'error'|'done', ...}
 */
export async function chat({ token, message, history, onEvent, signal }) {
  const r = await fetch(`${getApiBase()}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message, history }),
    signal,
  })

  if (r.status === 401) { onEvent({ type: 'expired' }); return }
  if (!r.ok) {
    const body = await r.json().catch(() => ({}))
    onEvent({ type: 'error', text: body.detail || `Server returned ${r.status}` })
    return
  }

  const reader = r.body.getReader()
  const decoder = new TextDecoder()
  let buf = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buf += decoder.decode(value, { stream: true })

    // SSE frames are separated by a blank line.
    const frames = buf.split('\n\n')
    buf = frames.pop()
    for (const frame of frames) {
      const line = frame.split('\n').find(l => l.startsWith('data: '))
      if (!line) continue
      try { onEvent(JSON.parse(line.slice(6))) } catch { /* skip partial */ }
    }
  }
}
