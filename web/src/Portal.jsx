import { useEffect, useRef } from 'react'

const money = (n) => n?.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })
const money2 = (n) => n?.toLocaleString('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 })
const day = (s) => new Date(s + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

export default function Portal({ data, tab, focus, onNavigate }) {
  if (!data) return <div className="pageload">Loading your portal</div>
  const P = { overview: Overview, accounts: Accounts, documents: Documents,
              tax: Tax, meetings: Meetings, forms: Forms }[tab] || Overview
  return <div className="page"><P data={data} focus={focus} onNavigate={onNavigate} /></div>
}

/* ------------------------------------------------------------------ pages */

function Overview({ data, onNavigate }) {
  const total = data.accounts.reduce((s, a) => s + a.balance, 0)
  const next = data.meetings.find(m => m.status === 'upcoming')
  const gaps = Object.entries(data.beneficiaries)
    .filter(([id, b]) => !b.length && !/Brokerage|Donor/.test(
      data.accounts.find(a => a.id === id)?.type || ''))
  return (
    <>
      <h1>Overview</h1>
      <div className="tiles">
        <div className="tile">
          <span className="tile-k">Total balance</span>
          <span className="tile-v">{money(total)}</span>
          <span className="tile-s">{data.accounts.length} accounts</span>
        </div>
        <div className="tile">
          <span className="tile-k">Next meeting</span>
          <span className="tile-v">{next ? day(next.date) : 'None scheduled'}</span>
          <span className="tile-s">{next ? `${next.type}, ${next.time}` : 'Ask Brooke to schedule one'}</span>
        </div>
        <div className="tile">
          <span className="tile-k">Advisory fee</span>
          <span className="tile-v">{data.fees.rate_pct}%</span>
          <span className="tile-s">{data.fees.frequency}, last {money(data.fees.last_amount)}</span>
        </div>
      </div>

      <h2>Your accounts</h2>
      <table className="tbl">
        <thead><tr><th>Account</th><th>Type</th><th className="r">Balance</th><th className="r">YTD</th></tr></thead>
        <tbody>
          {data.accounts.map(a => (
            <tr key={a.id} className="click" onClick={() => onNavigate('accounts', a.id)}>
              <td><code>{a.id}</code></td><td>{a.type}</td>
              <td className="r">{money(a.balance)}</td>
              <td className="r pos">+{a.ytd_return}%</td>
            </tr>
          ))}
        </tbody>
      </table>

      {gaps.length > 0 && (
        <div className="callout">
          <strong>No beneficiary named</strong> on {gaps.map(([id]) => id).join(', ')}.
          Ask Brooke how to add one, or open the form directly.
          <button className="gobtn sm" onClick={() => onNavigate('forms', 'beneficiary')}>
            Open Beneficiary Designation <span className="arrow">→</span>
          </button>
        </div>
      )}
    </>
  )
}

function Accounts({ data, focus, onNavigate }) {
  const sel = data.accounts.find(a => a.id === focus) || data.accounts[0]
  return (
    <>
      <h1>Accounts</h1>
      <div className="pills">
        {data.accounts.map(a => (
          <button key={a.id} className={`pill ${a.id === sel.id ? 'on' : ''}`}
                  onClick={() => onNavigate('accounts', a.id)}>
            {a.type}<em>{money(a.balance)}</em>
          </button>
        ))}
      </div>

      <div className="acct-head">
        <div><span className="tile-k">{sel.type}</span><code>{sel.id}</code></div>
        <div className="r"><span className="tile-v">{money(sel.balance)}</span>
          <span className="tile-s pos">+{sel.ytd_return}% YTD</span></div>
      </div>

      <h2>Holdings</h2>
      <table className="tbl">
        <thead><tr><th>Ticker</th><th>Name</th><th className="r">Shares</th><th className="r">Value</th><th className="r">Weight</th></tr></thead>
        <tbody>
          {(data.holdings[sel.id] || []).map(h => (
            <tr key={h.ticker}>
              <td><code>{h.ticker}</code></td><td>{h.name}</td>
              <td className="r">{h.shares.toLocaleString()}</td>
              <td className="r">{money(h.value)}</td><td className="r">{h.weight}%</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Recent activity</h2>
      <table className="tbl">
        <thead><tr><th>Date</th><th>Type</th><th>Description</th><th className="r">Amount</th></tr></thead>
        <tbody>
          {(data.activity[sel.id] || []).map((t, i) => (
            <tr key={i}>
              <td>{day(t.date)}</td><td>{t.type}</td><td>{t.description}</td>
              <td className={`r ${t.amount < 0 ? 'neg' : 'pos'}`}>{money2(t.amount)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Beneficiaries</h2>
      {(data.beneficiaries[sel.id] || []).length === 0
        ? <div className="callout">
            No beneficiary is named on this account.
            <button className="gobtn sm" onClick={() => onNavigate('forms', 'beneficiary')}>
              Name one <span className="arrow">→</span></button>
          </div>
        : <table className="tbl">
            <thead><tr><th>Name</th><th>Relationship</th><th>Tier</th><th className="r">Share</th></tr></thead>
            <tbody>
              {data.beneficiaries[sel.id].map((b, i) => (
                <tr key={i}><td>{b.name}</td><td>{b.relationship}</td><td>{b.tier}</td>
                  <td className="r">{b.share}%</td></tr>
              ))}
            </tbody>
          </table>}
    </>
  )
}

function Documents({ data }) {
  return (
    <>
      <h1>Documents</h1>
      <table className="tbl">
        <thead><tr><th>Document</th><th>Type</th><th>Date</th><th className="r"></th></tr></thead>
        <tbody>
          {data.documents.map((d, i) => (
            <tr key={i}>
              <td>{d.name}</td><td><span className="tag">{d.type}</span></td>
              <td>{day(d.date)}</td>
              <td className="r"><button className="ghost-btn sm" title="Demo, no file attached">Download</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="tiny">Statements post about 5 business days after each quarter ends.</p>
    </>
  )
}

function Tax({ data }) {
  const years = Object.entries(data.tax_returns)
  return (
    <>
      <h1>Tax</h1>
      <table className="tbl">
        <thead><tr><th>Year</th><th>Filing status</th><th className="r">AGI</th>
          <th className="r">Federal</th><th className="r">State</th><th className="r">Effective</th></tr></thead>
        <tbody>
          {years.map(([y, t]) => (
            <tr key={y}><td><strong>{y}</strong></td><td>{t.filing_status}</td>
              <td className="r">{money(t.agi)}</td><td className="r">{money(t.federal_tax)}</td>
              <td className="r">{money(t.state_tax)}</td><td className="r">{t.effective_rate}%</td></tr>
          ))}
        </tbody>
      </table>
      {Object.entries(data.contributions).map(([yr, accts]) => (
        <div key={yr}>
          <h2>{yr} contribution room</h2>
          <table className="tbl">
            <thead><tr><th>Account</th><th>Type</th><th className="r">Contributed</th>
              <th className="r">Limit</th><th className="r">Remaining</th></tr></thead>
            <tbody>
              {Object.entries(accts).map(([id, r]) => (
                <tr key={id}><td><code>{id}</code></td><td>{r.type}</td>
                  <td className="r">{money(r.contributed)}</td><td className="r">{money(r.limit)}</td>
                  <td className="r pos">{money(Math.max(0, r.limit - r.contributed))}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
      <p className="tiny">Limits shown are demo values, not tax advice.</p>
    </>
  )
}

function Meetings({ data }) {
  const up = data.meetings.filter(m => m.status === 'upcoming')
  const req = data.meetings.filter(m => m.status === 'requested')
  const past = data.meetings.filter(m => m.status !== 'upcoming' && m.status !== 'requested')
  return (
    <>
      <h1>Meetings</h1>
      {req.length > 0 && <>
        <h2>Requested</h2>
        {req.map((m, i) => (
          <div key={'r' + i} className="rowcard">
            <div><strong>{m.type}</strong>
              <span className="tile-s">
                {m.date !== 'TBD' ? `${m.date} at ${m.time}` : 'Office will call to find a time'}
                {m.topic ? ` · ${m.topic}` : ''}
              </span></div>
            <span className="tag warn-tag">Requested</span>
          </div>
        ))}
      </>}
      <h2>Upcoming</h2>
      {up.length === 0 ? <p className="muted">Nothing scheduled.</p> : up.map((m, i) => (
        <div key={i} className="rowcard">
          <div><strong>{m.type}</strong><span className="tile-s">{day(m.date)} at {m.time}</span></div>
          <span className="tag on">Upcoming</span>
        </div>
      ))}
      <button className="btn" style={{ marginTop: 14 }}>Request a meeting</button>
      <h2>Past</h2>
      {past.map((m, i) => (
        <div key={i} className="rowcard">
          <div><strong>{m.type}</strong><span className="tile-s">{day(m.date)} at {m.time}</span></div>
          <span className="tag">Completed</span>
        </div>
      ))}
    </>
  )
}

function Forms({ data, focus }) {
  const ref = useRef(null)
  useEffect(() => {
    if (focus && ref.current) ref.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [focus])
  return (
    <>
      <h1>Forms</h1>
      <p className="muted">Complete and sign electronically. Ask Brooke if you are not sure which one you need.</p>
      <div className="formgrid">
        {Object.entries(data.forms).map(([key, f]) => (
          <div key={key} ref={key === focus ? ref : null}
               className={`formcard ${key === focus ? 'focus' : ''}`}>
            <strong>{f.name}</strong>
            <p>{f.why}</p>
            <span className="tile-s">Turnaround: {f.turnaround}</span>
            <button className="btn sm">Start form</button>
          </div>
        ))}
      </div>
    </>
  )
}
