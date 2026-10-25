import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import client from '../api/client'

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (d.getFullYear() === 1900) return '-'
  const date = d.toLocaleDateString('it-IT')
  const time = d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
  return `${date} ${time}`
}

function fmt(v) {
  if (v === null || v === undefined) return '-'
  return v
}

const STICKY = 'sticky z-10'  // body: sticky left
const STICKY_COUNT = 2  // data, partita

const STAT_COLS = [
  { key: 'points',              label: 'PTS' },
  { key: 'minutes',             label: 'MIN', render: v => v != null ? Number(v).toFixed(2) : '-' },
  { key: 'two_pts_made',        label: '2P' },
  { key: 'two_pts_attempted',   label: '2PA' },
  { key: 'two_pts_perc',        label: '2P%', render: v => v != null ? Number(v).toFixed(2) : '-' },
  { key: 'dunks',               label: 'DNK' },
  { key: 'three_pts_made',      label: '3P' },
  { key: 'three_pts_attempted', label: '3PA' },
  { key: 'three_pts_perc',      label: '3P%', render: v => v != null ? Number(v).toFixed(2) : '-' },
  { key: 'ft_made',             label: 'FT' },
  { key: 'ft_attempted',        label: 'FTA' },
  { key: 'ft_perc',             label: 'FT%', render: v => v != null ? Number(v).toFixed(2) : '-' },
  { key: 'off_rebounds',        label: 'ORB' },
  { key: 'def_rebounds',        label: 'DRB' },
  { key: 'tot_rebounds',        label: 'TRB' },
  { key: 'blocks_given',        label: 'BLK+' },
  { key: 'blocks_received',     label: 'BLK-' },
  { key: 'turnovers',           label: 'TOV' },
  { key: 'steals',              label: 'STL' },
  { key: 'assists',             label: 'AST' },
  { key: 'fouls_committed',     label: 'FC' },
  { key: 'fouls_received',      label: 'FD' },
  { key: 'league_rating',       label: 'VAL' },
  { key: 'oer_rating',          label: 'OER', render: v => v != null ? Number(v).toFixed(2) : '-' },
  { key: 'plus_minus',          label: '+/-' },
]

export default function PlayerDetailPage() {
  const { name } = useParams()
  const navigate = useNavigate()
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stickyLefts, setStickyLefts] = useState([])
  const [hoveredRow, setHoveredRow] = useState(null)
  const [sortAsc, setSortAsc] = useState(true)
  const headerRefs = useRef([])

  const playerName = decodeURIComponent(name)

  useEffect(() => {
    setLoading(true)
    client.get(`/players/${encodeURIComponent(playerName)}/details`)
      .then(res => setRows(res.data))
      .catch(() => setError('Errore nel caricamento dei dati giocatore.'))
      .finally(() => setLoading(false))
  }, [playerName])

  useEffect(() => {
    const lefts = []
    let acc = 0
    for (let i = 0; i < STICKY_COUNT; i++) {
      lefts.push(acc)
      if (headerRefs.current[i]) acc += headerRefs.current[i].offsetWidth
    }
    setStickyLefts(lefts)
  }, [rows])

  const getStickyStyle = (i) =>
    stickyLefts[i] !== undefined ? { left: stickyLefts[i] } : {}

  const sortedRows = [...rows].sort((a, b) => {
    const da = new Date(a.game?.game_date ?? 0)
    const db = new Date(b.game?.game_date ?? 0)
    return sortAsc ? da - db : db - da
  })

  if (loading) return <p className="text-slate-500 dark:text-slate-400 text-sm">Caricamento...</p>
  if (error) return <p className="text-red-500 text-sm">{error}</p>

  return (
    <div>
      <button onClick={() => navigate(-1)} className="text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 text-sm mb-4 inline-flex items-center gap-1 transition-colors">
        ← Torna alla partita
      </button>

      <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight mb-1">{playerName}</h1>
      <p className="text-slate-500 dark:text-slate-400 text-sm mb-6">{rows.length} presenze</p>

      {rows.length === 0 && <p className="text-slate-500 dark:text-slate-400 text-sm">Nessuna statistica trovata.</p>}

      {rows.length > 0 && (
        <div className="rounded-xl ring-1 ring-slate-200 dark:ring-slate-700 shadow-sm overflow-auto max-h-[75vh]">
          <table className="text-xs min-w-max">
            <thead className="bg-slate-800 text-white">
              <tr>
                <th
                  ref={el => { headerRefs.current[0] = el }}
                  className="px-2 py-2 text-left whitespace-nowrap text-xs font-semibold uppercase tracking-wider bg-slate-700 sticky top-0 z-30 cursor-pointer select-none"
                  style={getStickyStyle(0)}
                  onClick={() => setSortAsc(v => !v)}
                >
                  Data {sortAsc ? '↑' : '↓'}
                </th>
                <th ref={el => { headerRefs.current[1] = el }} className="px-2 py-2 text-left whitespace-nowrap text-xs font-semibold uppercase tracking-wider bg-slate-700 sticky top-0 z-30" style={getStickyStyle(1)}>Partita</th>
                <th className="px-2 py-2 text-center whitespace-nowrap text-xs font-semibold uppercase tracking-wider sticky top-0 z-20 bg-slate-700">Tit</th>
                <th className="px-2 py-2 text-center whitespace-nowrap text-xs font-semibold uppercase tracking-wider sticky top-0 z-20 bg-slate-700">#</th>
                {STAT_COLS.map(col => (
                  <th key={col.key} className="px-2 py-2 text-center whitespace-nowrap text-xs font-semibold uppercase tracking-wider sticky top-0 z-20 bg-slate-700">{col.label}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {sortedRows.map((row) => {
                const isHovered = hoveredRow === row.id
                const stickyBg = isHovered ? 'bg-amber-50 dark:bg-slate-700' : 'bg-white dark:bg-slate-900'
                return (
                <tr
                  key={row.id}
                  className={`cursor-pointer ${isHovered ? 'bg-amber-50 dark:bg-slate-700' : 'bg-white dark:bg-slate-900'}`}
                  onClick={() => navigate(`/games/${row.game.id}`)}
                  onMouseEnter={() => setHoveredRow(row.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                >
                  <td className={`px-2 py-1 whitespace-nowrap ${STICKY} ${stickyBg}`} style={getStickyStyle(0)}>{formatDate(row.game.game_date)}</td>
                  <td className={`px-2 py-1 whitespace-nowrap font-medium ${STICKY} ${stickyBg}`} style={getStickyStyle(1)}>
                    {row.game.home_team} {row.game.score} {row.game.away_team}
                  </td>
                  <td className="px-2 py-1 text-center">{row.starter ? '✓' : ''}</td>
                  <td className="px-2 py-1 text-center">{fmt(row.number)}</td>
                  {STAT_COLS.map(col => (
                    <td key={col.key} className="px-2 py-1 text-center">
                      {col.render ? col.render(row[col.key]) : fmt(row[col.key])}
                    </td>
                  ))}
                </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
