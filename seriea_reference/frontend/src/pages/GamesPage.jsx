import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import client from '../api/client'

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (d.getFullYear() === 1900) return '-'
  const date = d.toLocaleDateString('it-IT')
  const time = d.toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })
  return `${date} ${time}`
}

function SortIcon({ field, sortField, sortDir }) {
  if (sortField !== field) return null
  return <span className="ml-1">{sortDir === 'asc' ? '↑' : '↓'}</span>
}

export default function GamesPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [games, setGames] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [sortField, setSortField] = useState(null)
  const [sortDir, setSortDir] = useState('asc')

  const season = searchParams.get('season')
  const team = searchParams.get('team')
  const teamTwo = searchParams.get('team_two')
  const onlyHome = searchParams.get('only_home') === 'true'
  const onlyAway = searchParams.get('only_away') === 'true'

  useEffect(() => {
    setLoading(true)
    setError(null)
    const params = {}
    if (season) params.season = season
    if (team) params.team = team
    if (teamTwo) params.team_two = teamTwo
    if (onlyHome) params.only_home = true
    if (onlyAway) params.only_away = true

    client.get('/games', { params })
      .then(res => setGames(res.data))
      .catch(() => setError('Errore nel caricamento delle partite.'))
      .finally(() => setLoading(false))
  }, [season, team, teamTwo, onlyHome, onlyAway])

  const subtitle = [
    season || 'Tutte le stagioni',
    team && teamTwo ? `${team} vs ${teamTwo}` : (team || teamTwo || 'Tutte le squadre'),
    onlyHome ? '(solo in casa)' : onlyAway ? '(solo in trasferta)' : '',
  ].filter(Boolean).join(' — ')

  function handleSort(field) {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir('asc')
    }
  }

  const sortedGames = [...games].sort((a, b) => {
    if (!sortField) return 0
    let va = a[sortField]
    let vb = b[sortField]
    if (sortField === 'game_date') {
      va = va ? new Date(va).getTime() : 0
      vb = vb ? new Date(vb).getTime() : 0
    } else {
      va = va ?? ''
      vb = vb ?? ''
    }
    if (va < vb) return sortDir === 'asc' ? -1 : 1
    if (va > vb) return sortDir === 'asc' ? 1 : -1
    return 0
  })

  return (
    <div>
      <div className="mb-6">
        <button onClick={() => navigate('/')} className="text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 text-sm mb-3 inline-flex items-center gap-1 transition-colors">
          ← Nuova ricerca
        </button>
        <div className="flex items-baseline gap-3">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">{subtitle}</h1>
          {!loading && (
            <span className="text-sm text-slate-400 dark:text-slate-500">{games.length} partite</span>
          )}
        </div>
      </div>

      {loading && <p className="text-slate-500 dark:text-slate-400 text-sm">Caricamento...</p>}
      {error && <p className="text-red-500 text-sm">{error}</p>}

      {!loading && !error && games.length === 0 && (
        <p className="text-slate-500 dark:text-slate-400 text-sm">Nessuna partita trovata.</p>
      )}

      {!loading && games.length > 0 && (
        <div className="rounded-xl overflow-auto max-h-[75vh] ring-1 ring-slate-200 dark:ring-slate-700 shadow-sm">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-700 text-white sticky top-0 z-10">
              <tr>
                <th
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider cursor-pointer select-none hover:bg-slate-700 transition-colors"
                  onClick={() => handleSort('season')}
                >
                  Stagione<SortIcon field="season" sortField={sortField} sortDir={sortDir} />
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Giornata</th>
                <th
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider cursor-pointer select-none hover:bg-slate-700 transition-colors"
                  onClick={() => handleSort('game_date')}
                >
                  Data<SortIcon field="game_date" sortField={sortField} sortDir={sortDir} />
                </th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Squadra di Casa</th>
                <th className="px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider">Risultato</th>
                <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider">Squadra Ospite</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {sortedGames.map((g) => (
                <tr
                  key={g.id}
                  className="bg-white dark:bg-slate-900 hover:bg-amber-50 dark:hover:bg-slate-700 cursor-pointer transition-colors"
                  onClick={() => navigate(`/games/${g.id}`)}
                >
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{g.season ?? '-'}</td>
                  <td className="px-4 py-3 text-slate-500 dark:text-slate-400">{g.matchday ?? '-'}</td>
                  <td className="px-4 py-3 text-slate-600 dark:text-slate-300">{formatDate(g.game_date)}</td>
                  <td className="px-4 py-3 font-medium text-slate-800 dark:text-slate-200">{g.home_team}</td>
                  <td className="px-4 py-3 text-center font-bold text-slate-900 dark:text-slate-100">{g.score ?? '-'}</td>
                  <td className="px-4 py-3 font-medium text-slate-800 dark:text-slate-200">{g.away_team}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
