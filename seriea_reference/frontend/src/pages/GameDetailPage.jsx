import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import client from '../api/client'

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (d.getFullYear() === 1900) return '-'
  const date = d.toLocaleDateString('it-IT')
  const time = d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
  return `${date} ${time}`
}

const STICKY = 'sticky z-10'
const STICKY_COUNT = 4  // team, starter, number, player

const STAT_COLS = [
  { key: 'team',    label: 'Squadra', sticky: true },
  { key: 'starter', label: 'Tit', sticky: true, render: v => v ? '✓' : '' },
  { key: 'number',  label: '#', sticky: true },
  { key: 'player',  label: 'Giocatore', sticky: true, isPlayer: true },
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
  { key: 'fouls_committed',     label: 'PF' },
  { key: 'fouls_received',      label: 'FD' },
  { key: 'league_rating',       label: 'VAL' },
  { key: 'oer_rating',          label: 'OER', render: v => v != null ? Number(v).toFixed(2) : '-' },
  { key: 'plus_minus',          label: '+/-' },
]

function fmt(v) {
  if (v === null || v === undefined) return '-'
  return v
}

export default function GameDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [game, setGame] = useState(null)
  const [details, setDetails] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stickyLefts, setStickyLefts] = useState([])
  const [hoveredRow, setHoveredRow] = useState(null)
  const headerRefs = useRef([])

  useEffect(() => {
    Promise.all([
      client.get(`/games/${id}`),
      client.get(`/games/${id}/details`),
    ])
      .then(([gameRes, detailsRes]) => {
        setGame(gameRes.data)
        setDetails(detailsRes.data)
      })
      .catch(() => setError('Errore nel caricamento della partita.'))
      .finally(() => setLoading(false))
  }, [id])

  // Calcola gli offset left delle colonne sticky dopo il render
  useEffect(() => {
    const lefts = []
    let acc = 0
    for (let i = 0; i < STICKY_COUNT; i++) {
      lefts.push(acc)
      if (headerRefs.current[i]) acc += headerRefs.current[i].offsetWidth
    }
    setStickyLefts(lefts)
  }, [details])

  const getStickyStyle = (colIndex) =>
    stickyLefts[colIndex] !== undefined ? { left: stickyLefts[colIndex] } : {}

  if (loading) return <p className="text-slate-500 dark:text-slate-400 text-sm">Caricamento...</p>
  if (error) return <p className="text-red-500 text-sm">{error}</p>

  return (
    <div>
      <button onClick={() => navigate(-1)} className="text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 text-sm mb-4 inline-flex items-center gap-1 transition-colors">
        ← Torna alla lista
      </button>

      {game && (
        <div className="mb-6 bg-white dark:bg-slate-800 rounded-xl ring-1 ring-slate-200 dark:ring-slate-700 shadow-sm px-6 py-5">
          <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-3">
            {game.season} &mdash; {game.matchday}
          </p>
          <div className="flex items-center gap-4 flex-wrap">
            <span className="text-xl font-bold text-slate-900 dark:text-slate-100">{game.home_team}</span>
            <span className="text-2xl font-black text-orange-500 min-w-[4rem] text-center">{game.score}</span>
            <span className="text-xl font-bold text-slate-900 dark:text-slate-100">{game.away_team}</span>
          </div>
          <p className="text-slate-400 dark:text-slate-500 text-xs mt-2">{formatDate(game.game_date)}</p>
        </div>
      )}

      {details.length === 0 && <p className="text-slate-500 dark:text-slate-400 text-sm">Nessuna statistica disponibile.</p>}

      {details.length > 0 && (
        <div className="overflow-x-auto rounded-xl ring-1 ring-slate-200 dark:ring-slate-700 shadow-sm">
          <table className="text-xs min-w-max">
            <thead className="bg-slate-700 text-white">
              <tr>
                {STAT_COLS.map((col, ci) => (
                  <th
                    key={col.key}
                    ref={col.sticky ? el => { headerRefs.current[ci] = el } : null}
                    className={`px-2 py-2 text-center whitespace-nowrap text-xs font-semibold uppercase tracking-wider bg-slate-700 ${col.sticky ? STICKY : ''}`}
                    style={col.sticky ? getStickyStyle(ci) : {}}
                  >{col.label}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {details.map((row, i) => {
                const isTotals = row.player === 'Totali'
                const isHovered = hoveredRow === row.id
                const baseBg = isTotals ? 'bg-slate-100 dark:bg-slate-700' : 'bg-white dark:bg-slate-900'
                const rowClass = `${isTotals ? 'font-bold' : ''} ${isHovered ? 'bg-amber-50 dark:bg-slate-700' : baseBg}`
                return (
                <tr
                  key={row.id}
                  className={rowClass}
                  onMouseEnter={() => setHoveredRow(row.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                >
                  {STAT_COLS.map((col, ci) => {
                    const isSpecialRow = row.player === 'Totali' || row.player === 'Squadra'
                    const stickyBg = isHovered ? 'bg-amber-50 dark:bg-slate-700' : isTotals ? 'bg-slate-100 dark:bg-slate-700' : 'bg-white dark:bg-slate-900'
                    return (
                    <td key={col.key}
                      className={`px-2 py-1 text-center whitespace-nowrap ${col.sticky ? `${STICKY} ${stickyBg}` : ''}`}
                      style={col.sticky ? getStickyStyle(ci) : {}}
                    >
                      {col.isPlayer && !isSpecialRow ? (
                        <Link
                          to={`/players/${encodeURIComponent(row.player)}`}
                          className="text-orange-600 dark:text-orange-400 hover:text-orange-800 dark:hover:text-orange-300 hover:underline font-medium"
                        >
                          {row.player}
                        </Link>
                      ) : col.render ? col.render(row[col.key]) : fmt(row[col.key])}
                    </td>
                  )})}
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
