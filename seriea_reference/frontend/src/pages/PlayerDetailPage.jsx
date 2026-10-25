import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import client from '../api/client'

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (d.getFullYear() === 1900) return '-'
  return d.toLocaleDateString('it-IT')
}

function fmt(v) {
  if (v === null || v === undefined) return '-'
  return v
}

const STICKY = 'sticky z-10'
const STICKY_COUNT = 2  // data, partita

const STAT_COLS = [
  { key: 'points',              label: 'Pts' },
  { key: 'minutes',             label: 'Min', render: v => v != null ? Number(v).toFixed(2) : '-' },
  { key: 'two_pts_made',        label: '2P' },
  { key: 'two_pts_attempted',   label: '2PA' },
  { key: 'two_pts_perc',        label: '2P%', render: v => v != null ? Number(v).toFixed(2) : '-' },
  { key: 'dunks',               label: 'Sch' },
  { key: 'three_pts_made',      label: '3P' },
  { key: 'three_pts_attempted', label: '3PA' },
  { key: 'three_pts_perc',      label: '3P%', render: v => v != null ? Number(v).toFixed(2) : '-' },
  { key: 'ft_made',             label: 'TL' },
  { key: 'ft_attempted',        label: 'TLA' },
  { key: 'ft_perc',             label: 'TL%', render: v => v != null ? Number(v).toFixed(2) : '-' },
  { key: 'off_rebounds',        label: 'OR' },
  { key: 'def_rebounds',        label: 'DR' },
  { key: 'tot_rebounds',        label: 'TR' },
  { key: 'blocks_given',        label: 'Blk+' },
  { key: 'blocks_received',     label: 'Blk-' },
  { key: 'turnovers',           label: 'PP' },
  { key: 'steals',              label: 'PR' },
  { key: 'assists',             label: 'Ast' },
  { key: 'fouls_committed',     label: 'FC' },
  { key: 'fouls_received',      label: 'FS' },
  { key: 'league_rating',       label: 'Val' },
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

  if (loading) return <p className="text-gray-500">Caricamento...</p>
  if (error) return <p className="text-red-500">{error}</p>

  return (
    <div>
      <button onClick={() => navigate(-1)} className="text-blue-700 hover:underline text-sm mb-4 block">
        ← Torna alla partita
      </button>

      <h1 className="text-2xl font-bold mb-1">{playerName}</h1>
      <p className="text-gray-500 text-sm mb-6">{rows.length} presenze</p>

      {rows.length === 0 && <p className="text-gray-500">Nessuna statistica trovata.</p>}

      {rows.length > 0 && (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="text-xs min-w-max">
            <thead className="bg-blue-800 text-white">
              <tr>
                <th ref={el => { headerRefs.current[0] = el }} className={`px-2 py-2 text-left whitespace-nowrap bg-blue-800 ${STICKY}`} style={getStickyStyle(0)}>Data</th>
                <th ref={el => { headerRefs.current[1] = el }} className={`px-2 py-2 text-left whitespace-nowrap bg-blue-800 ${STICKY}`} style={getStickyStyle(1)}>Partita</th>
                <th className="px-2 py-2 text-center whitespace-nowrap">Tit</th>
                <th className="px-2 py-2 text-center whitespace-nowrap">#</th>
                {STAT_COLS.map(col => (
                  <th key={col.key} className="px-2 py-2 text-center whitespace-nowrap">{col.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => {
                const isHovered = hoveredRow === row.id
                const baseBg = i % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                const stickyBg = isHovered ? 'bg-yellow-100' : baseBg
                return (
                <tr
                  key={row.id}
                  className={`cursor-pointer ${isHovered ? 'bg-yellow-100' : baseBg}`}
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
