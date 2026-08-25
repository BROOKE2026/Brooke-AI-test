// Talks to the Brooke API. The base URL is stored in localStorage so the
// published site never needs rebuilding when the tunnel URL changes.

const KEY = 'brooke.apiBase'

export function getApiBase() {
  // Precedence: whatever the user typed in Connection settings, then the URL
  // baked in at build time (VITE_API_BASE), then a local dev server.
  return localStorage.getItem(KEY)
      || import.meta.env.VITE_API_BASE
      || 'http://localhost:8080'
}
export function setApiBase(url) {
  localStorage.setItem(KEY, url.replace(/\/+$/, ''))
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
    const body = await r.json().catch(() => ({}))
    throw new Error(body.detail || 'Sign in failed')
  }
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
