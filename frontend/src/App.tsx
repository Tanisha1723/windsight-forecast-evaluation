
import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Download,
  RefreshCw,
  Wind,
  Zap,
} from 'lucide-react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'

type Result = {
  startTime: string
  actual: number
  forecast: number | null
  publishTime: string | null
  error: number | null
  status: string
}

type Metrics = {
  interval_count: number
  mae: number | null
  rmse: number | null
  bias: number | null
  wape: number | null
}

type Evaluation = {
  start_date: string
  end_date: string
  cutoff_hours: number
  interval_count: number
  evaluated_count: number
  unavailable_count: number
  metrics: Metrics
  results: Result[]
}

function formatNumber(value: number | null | undefined, digits = 0) {
  if (value == null || !Number.isFinite(value)) return '—'
  return value.toLocaleString('en-GB', {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })
}

function formatTime(value: string | null | undefined) {
  if (!value) return '—'
  return new Date(value).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
    timeZoneName: 'short',
  })
}

function formatHour(value: string) {
  return new Date(value).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    timeZone: 'UTC',
  })
}

function MetricCard({
  label,
  value,
  unit,
  detail,
  icon: Icon,
  tone = 'blue',
}: {
  label: string
  value: string
  unit: string
  detail: string
  icon: typeof Activity
  tone?: 'blue' | 'orange' | 'green' | 'purple'
}) {
  return (
    <article className="metric-card">
      <div className="metric-top">
        <span className="metric-label">{label}</span>
        <span className={`metric-icon ${tone}`}><Icon size={18} /></span>
      </div>
      <div className="metric-value">{value}<span>{unit}</span></div>
      <p className="metric-detail">{detail}</p>
    </article>
  )
}

function App() {
  const [startDate, setStartDate] = useState('2026-01-01')
  const [endDate, setEndDate] = useState('2026-01-31')
  const [cutoffHours, setCutoffHours] = useState(24)
  const [data, setData] = useState<Evaluation | null>(null)
  const [loading, setLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [page, setPage] = useState(1)
  const pageSize = 15

  const loadData = useCallback(async () => {
    if (endDate < startDate) {
      setErrorMessage('End date must be on or after start date.')
      return
    }

    setLoading(true)
    setErrorMessage('')

    try {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        cutoff_hours: String(cutoffHours),
      })

      const response = await fetch(`${API_BASE}/api/evaluate?${params}`)
      if (!response.ok) {
        const body = await response.json().catch(() => null)
        throw new Error(body?.detail || `Request failed (${response.status})`)
      }

      const result: Evaluation = await response.json()
      setData(result)
      setLastUpdated(new Date())
      setPage(1)
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? `${error.message}. Make sure the FastAPI backend is running.`
          : 'Unable to load evaluation data.',
      )
    } finally {
      setLoading(false)
    }
  }, [startDate, endDate, cutoffHours])

  useEffect(() => {
    void loadData()
  }, [loadData])

  const chartData = useMemo(
    () =>
      (data?.results ?? [])
        .filter((row) => row.status === 'evaluated' && row.forecast != null)
        .map((row) => ({
          time: row.startTime,
          label: formatHour(row.startTime),
          actual: row.actual,
          forecast: row.forecast as number,
        })),
    [data],
  )

  const pageCount = Math.max(1, Math.ceil((data?.results.length ?? 0) / pageSize))
  const visibleRows = (data?.results ?? []).slice(
    (page - 1) * pageSize,
    page * pageSize,
  )

  function exportCsv() {
    if (!data?.results.length) return

    const headers = [
      'Delivery time (UTC)',
      'Actual generation (MW)',
      'Forecast generation (MW)',
      'Forecast error (MW)',
      'Forecast publish time (UTC)',
      'Status',
    ]

    const rows = data.results.map((row) => [
      row.startTime,
      row.actual,
      row.forecast ?? '',
      row.error ?? '',
      row.publishTime ?? '',
      row.status,
    ])

    const csv = [headers, ...rows]
      .map((row) =>
        row.map((cell) => `"${String(cell).replace(/"/g, '""')}"`).join(','),
      )
      .join('\r\n')

    const url = URL.createObjectURL(
      new Blob([csv], { type: 'text/csv;charset=utf-8;' }),
    )
    const link = document.createElement('a')
    link.href = url
    link.download = `windsight-${startDate}-to-${endDate}.csv`
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
  }

  const metrics = data?.metrics

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" aria-label="WindSight home">
          <span className="brand-mark"><Wind size={23} /></span>
          <span>WindSight<small>ENERGY INTELLIGENCE</small></span>
        </a>

        <div className="nav-section-label">WORKSPACE</div>
        <div className="nav-item active"><BarChart3 size={18} /> Forecast evaluation</div>

        <div className="sidebar-bottom">
          <div className="sidebar-status"><span className="status-dot" /> API connection</div>
          <p>UK wind generation<br />Day-ahead decision support</p>
          <div className="sidebar-version">WINDSIGHT · PROTOTYPE 0.1</div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">Workspace <span>/</span> Forecast evaluation</div>
          <div className="topbar-right">
            <span className="live-indicator"><span /> Historical analysis</span>
            <span className="avatar">WS</span>
          </div>
        </header>

        <div className="dashboard">
          <section className="page-heading">
            <div>
              <div className="eyebrow"><span /> RENEWABLES INTELLIGENCE</div>
              <h1>Wind forecast performance</h1>
              <p className="page-description">
                Understand forecast error before making day-ahead purchasing decisions.
              </p>
            </div>
            <button className="button-secondary" onClick={() => void loadData()} disabled={loading}>
              <RefreshCw size={15} className={loading ? 'spin' : ''} />
              Refresh data
            </button>
          </section>

          <section className="filter-panel">
            <div className="filter-heading">
              <div><CalendarDays size={17} /><span>Evaluation settings</span></div>
              <span className="utc-label">All timestamps in UTC</span>
            </div>
            <div className="filter-controls">
              <label>
                <span>From date</span>
                <input type="date" value={startDate} max="2026-01-31" onChange={(e) => setStartDate(e.target.value)} />
              </label>
              <label>
                <span>To date</span>
                <input type="date" value={endDate} min={startDate} max="2026-01-31" onChange={(e) => setEndDate(e.target.value)} />
              </label>
              <label>
                <span>Decision cutoff</span>
                <select value={cutoffHours} onChange={(e) => setCutoffHours(Number(e.target.value))}>
                  <option value={12}>12 hours before delivery</option>
                  <option value={24}>24 hours before delivery</option>
                  <option value={36}>36 hours before delivery</option>
                  <option value={48}>48 hours before delivery</option>
                  <option value={72}>72 hours before delivery</option>
                </select>
              </label>
              <button className="button-primary" onClick={() => void loadData()} disabled={loading}>
                {loading ? <RefreshCw size={16} className="spin" /> : <Activity size={16} />}
                Run evaluation
              </button>
            </div>
          </section>

          {errorMessage && (
            <div className="error-banner"><AlertCircle size={19} /><div><strong>Could not load evaluation</strong><p>{errorMessage}</p></div></div>
          )}

          <section className="section-heading">
            <div><h2>Performance overview</h2><p>Forecasts matched to actual hourly wind generation</p></div>
            <span className="data-period"><Clock3 size={14} /> {startDate} — {endDate}</span>
          </section>

          <section className="metrics-grid">
            <MetricCard label="Mean absolute error" value={formatNumber(metrics?.mae, 0)} unit=" MW" detail="Average absolute forecast miss" icon={Activity} tone="blue" />
            <MetricCard label="Root mean square error" value={formatNumber(metrics?.rmse, 0)} unit=" MW" detail="Penalises larger forecast errors" icon={Zap} tone="orange" />
            <MetricCard label="Forecast bias" value={formatNumber(metrics?.bias, 0)} unit=" MW" detail={metrics?.bias == null ? 'No evaluated intervals' : metrics.bias > 0 ? 'Systematic overforecasting' : metrics.bias < 0 ? 'Systematic underforecasting' : 'No average directional bias'} icon={metrics?.bias != null && metrics.bias < 0 ? ArrowDownRight : ArrowUpRight} tone="purple" />
            <MetricCard label="Weighted absolute error" value={formatNumber(metrics?.wape, 1)} unit="%" detail="Absolute error relative to total actual" icon={BarChart3} tone="green" />
          </section>

          <div className="summary-strip">
            <div><CheckCircle2 size={17} /><span><strong>{formatNumber(data?.evaluated_count)}</strong> evaluated intervals</span></div>
            <span className="summary-divider" />
            <div><AlertCircle size={17} /><span><strong>{formatNumber(data?.unavailable_count)}</strong> unavailable forecasts</span></div>
            <span className="summary-divider" />
            <div><Activity size={17} /><span><strong>{formatNumber(data?.interval_count)}</strong> total intervals</span></div>
            {lastUpdated && <span className="updated-time">Updated {lastUpdated.toLocaleTimeString()}</span>}
          </div>

          <section className="content-card chart-card">
            <div className="card-heading">
              <div><h2>Forecast vs actual generation</h2><p>Hourly wind generation · MW</p></div>
              <div className="chart-legend-note"><span className="legend-dot actual-dot" /> Actual <span className="legend-dot forecast-dot" /> Forecast</div>
            </div>
            {loading && !data ? (
              <div className="empty-state"><RefreshCw className="spin" size={22} /><p>Loading evaluation data…</p></div>
            ) : chartData.length ? (
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData} margin={{ top: 12, right: 18, left: 8, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8edf3" />
                    <XAxis dataKey="time" tickFormatter={formatHour} minTickGap={45} tick={{ fontSize: 11, fill: '#7b8797' }} axisLine={false} tickLine={false} />
                    <YAxis tickFormatter={(value: number) => `${(value / 1000).toFixed(0)}k`} tick={{ fontSize: 11, fill: '#7b8797' }} axisLine={false} tickLine={false} width={42} />
                    <Tooltip
                      labelFormatter={(label) => `Delivery: ${formatTime(String(label))}`}
                      formatter={(value) => [`${formatNumber(Number(value))} MW`]}
                      contentStyle={{ border: '1px solid #e1e7ef', borderRadius: 10, fontSize: 12 }}
                    />
                    <Legend verticalAlign="top" align="right" height={30} />
                    <Line type="monotone" dataKey="actual" name="Actual" stroke="#0e9f8f" strokeWidth={2.2} dot={false} activeDot={{ r: 4 }} connectNulls={false} />
                    <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#5375dc" strokeWidth={2.2} dot={false} activeDot={{ r: 4 }} connectNulls={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="empty-state"><BarChart3 size={26} /><p>{loading ? 'Loading…' : 'No evaluated data for this selection.'}</p></div>
            )}
            <div className="chart-footer"><span><span className="legend-dot actual-dot" /> Actuals are hourly averages of two half-hourly observations.</span><span>Source: Elexon BMRS</span></div>
          </section>

          <section className="content-card audit-card">
            <div className="card-heading audit-heading">
              <div><h2>Forecast audit trail</h2><p>Review each delivery hour and the forecast available at the decision cutoff.</p></div>
              <button className="button-secondary export-button" onClick={exportCsv} disabled={!data?.results.length}><Download size={15} /> Export CSV</button>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Delivery time (UTC)</th><th>Actual (MW)</th><th>Forecast (MW)</th><th>Error (MW)</th><th>Published (UTC)</th><th>Status</th></tr></thead>
                <tbody>
                  {visibleRows.map((row) => (
                    <tr key={row.startTime}>
                      <td className="delivery-cell">{formatTime(row.startTime)}</td>
                      <td>{formatNumber(row.actual)}</td>
                      <td>{formatNumber(row.forecast)}</td>
                      <td className={row.error == null ? '' : row.error > 0 ? 'error-positive' : row.error < 0 ? 'error-negative' : ''}>{row.error == null ? '—' : `${row.error > 0 ? '+' : ''}${formatNumber(row.error)}`}</td>
                      <td className="published-cell">{formatTime(row.publishTime)}</td>
                      <td><span className={`status-pill ${row.status === 'evaluated' ? 'success' : 'warning'}`}>{row.status === 'evaluated' ? 'Evaluated' : 'No forecast'}</span></td>
                    </tr>
                  ))}
                  {!visibleRows.length && <tr><td colSpan={6} className="no-rows">{loading ? 'Loading results…' : 'No results to display.'}</td></tr>}
                </tbody>
              </table>
            </div>
            <div className="table-footer">
              <span>Showing {visibleRows.length ? (page - 1) * pageSize + 1 : 0}–{Math.min(page * pageSize, data?.results.length ?? 0)} of {formatNumber(data?.results.length)} intervals</span>
              <div className="pagination">
                <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>Previous</button>
                <span>Page {page} of {pageCount}</span>
                <button onClick={() => setPage((p) => Math.min(pageCount, p + 1))} disabled={page >= pageCount}>Next</button>
              </div>
            </div>
          </section>

          <section className="methodology-card">
            <div className="method-icon"><Activity size={19} /></div>
            <div>
              <h3>How to interpret these metrics</h3>
              <p><strong>Forecast error = forecast − actual.</strong> Positive bias indicates overforecasting; negative bias indicates underforecasting. MAE and RMSE are measured in MW, while WAPE is a percentage of total actual generation.</p>
              <p>For each delivery hour, WindSight selects the latest forecast published at or before the configured cutoff. Actual generation is the average of the two half-hourly FUELHH observations. Only complete hours with an eligible forecast contribute to the metrics.</p>
              <p className="method-caveat">Decision-support note: these metrics quantify uncertainty in wind generation, not total procurement requirements. Demand, prices, interconnector flows, and other generation sources are not included.</p>
            </div>
          </section>

          <footer className="page-footer">
            <span>WindSight · Day-ahead wind forecast evaluation</span>
            <span>Data: Elexon BMRS · January 2026</span>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App
