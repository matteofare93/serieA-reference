import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import client from '../api/client'

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
  { key: 'fouls_received',      label: 'FS' },
  { key: 'league_rating',       label: 'Val' },
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

  if (loading) return <p className="text-gray-500">Caricamento...</p>
  if (error) return <p className="text-red-500">{error}</p>

  return (
    <div>
      <button onClick={() => navigate(-1)} className="text-blue-700 hover:underline text-sm mb-4 block">
        ← Torna alla lista
      </button>

      {game && (
        <div className="mb-6">
          <h1 className="text-2xl font-bold">
            {game.home_team} <span className="text-blue-700">{game.score}</span> {game.away_team}
          </h1>
          <p className="text-gray-500 text-sm mt-1">{game.season} — {game.matchday}</p>
        </div>
      )}

      {details.length === 0 && <p className="text-gray-500">Nessuna statistica disponibile.</p>}

      {details.length > 0 && (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="text-xs min-w-max">
            <thead className="bg-blue-800 text-white">
              <tr>
                {STAT_COLS.map((col, ci) => (
                  <th
                    key={col.key}
                    ref={col.sticky ? el => { headerRefs.current[ci] = el } : null}
                    className={`px-2 py-2 text-center whitespace-nowrap bg-blue-800 ${col.sticky ? STICKY : ''}`}
                    style={col.sticky ? getStickyStyle(ci) : {}}
                  >{col.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {details.map((row, i) => {
                const isTotals = row.player === 'Totali'
                const isHovered = hoveredRow === row.id
                const baseBg = isTotals ? 'bg-gray-300' : i % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                const rowClass = `${isTotals ? 'font-bold' : ''} ${isHovered ? 'bg-yellow-100' : baseBg}`
                return (
                <tr
                  key={row.id}
                  className={rowClass}
                  onMouseEnter={() => setHoveredRow(row.id)}
                  onMouseLeave={() => setHoveredRow(null)}
                >
                  {STAT_COLS.map((col, ci) => {
                    const isSpecialRow = row.player === 'Totali' || row.player === 'Squadra'
                    const stickyBg = isHovered ? 'bg-yellow-100' : isTotals ? 'bg-gray-300' : i % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                    return (
                    <td key={col.key}
                      className={`px-2 py-1 text-center whitespace-nowrap ${col.sticky ? `${STICKY} ${stickyBg}` : ''}`}
                      style={col.sticky ? getStickyStyle(ci) : {}}
                    >
                      {col.isPlayer && !isSpecialRow ? (
                        <Link
                          to={`/players/${encodeURIComponent(row.player)}`}
                          className="text-blue-700 hover:underline font-medium"
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
