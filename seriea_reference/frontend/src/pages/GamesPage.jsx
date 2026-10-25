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

export default function GamesPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [games, setGames] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

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

  return (
    <div>
      <div className="flex items-center gap-4 mb-4">
        <button onClick={() => navigate('/')} className="text-blue-700 hover:underline text-sm">← Nuova ricerca</button>
        <h1 className="text-xl font-bold">{subtitle}</h1>
        <span className="text-gray-400 text-sm">{loading ? '' : `${games.length} partite`}</span>
      </div>

      {loading && <p className="text-gray-500">Caricamento...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && !error && games.length === 0 && (
        <p className="text-gray-500">Nessuna partita trovata.</p>
      )}

      {!loading && games.length > 0 && (
        <div className="overflow-x-auto rounded border border-gray-200">
          <table className="min-w-full text-sm">
            <thead className="bg-blue-800 text-white">
              <tr>
                <th className="px-3 py-2 text-left">Stagione</th>
                <th className="px-3 py-2 text-left">Giornata</th>
                <th className="px-3 py-2 text-left">Data</th>
                <th className="px-3 py-2 text-left">Squadra di Casa</th>
                <th className="px-3 py-2 text-center">Risultato</th>
                <th className="px-3 py-2 text-left">Squadra Ospite</th>
              </tr>
            </thead>
            <tbody>
              {games.map((g, i) => (
                <tr
                  key={g.id}
                  className={`cursor-pointer hover:bg-yellow-100 ${i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}
                  onClick={() => navigate(`/games/${g.id}`)}
                >
                  <td className="px-3 py-2">{g.season ?? '-'}</td>
                  <td className="px-3 py-2">{g.matchday ?? '-'}</td>
                  <td className="px-3 py-2">{formatDate(g.game_date)}</td>
                  <td className="px-3 py-2 font-medium">{g.home_team}</td>
                  <td className="px-3 py-2 text-center font-bold">{g.score ?? '-'}</td>
                  <td className="px-3 py-2 font-medium">{g.away_team}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
