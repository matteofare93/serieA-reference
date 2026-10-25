import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

export default function SearchPage() {
  const navigate = useNavigate()
  const [seasons, setSeasons] = useState([])
  const [season, setSeason] = useState('')
  const [team, setTeam] = useState('')
  const [teamTwo, setTeamTwo] = useState('')
  const [onlyHome, setOnlyHome] = useState(false)
  const [onlyAway, setOnlyAway] = useState(false)

  useEffect(() => {
    client.get('/seasons').then(res => {
      setSeasons(res.data)
      if (res.data.length > 0) setSeason('All')
    })
  }, [])

  function handleSubmit(e) {
    e.preventDefault()
    const params = new URLSearchParams()
    if (season && season !== 'All') params.set('season', season)
    if (team.trim()) params.set('team', team.trim())
    if (teamTwo.trim()) params.set('team_two', teamTwo.trim())
    if (onlyHome) params.set('only_home', 'true')
    if (onlyAway) params.set('only_away', 'true')
    navigate('/games?' + params.toString())
  }

  return (
    <div className="max-w-lg">
      <h1 className="text-2xl font-bold mb-1">Ricerca Partite</h1>
      <p className="text-gray-500 mb-6 text-sm">
        Cerca per stagione e/o squadra. Lascia i campi vuoti per vedere tutto.
      </p>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {/* Stagione */}
        <div>
          <label className="block text-sm font-medium mb-1">Stagione</label>
          <select
            value={season}
            onChange={e => setSeason(e.target.value)}
            className="border border-gray-300 rounded px-3 py-2 w-full bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="All">Tutte le stagioni</option>
            {seasons.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {/* Team 1 */}
        <div>
          <label className="block text-sm font-medium mb-1">Squadra</label>
          <input
            type="text"
            value={team}
            onChange={e => setTeam(e.target.value)}
            placeholder="es. Varese"
            className="border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Checkboxes */}
        <div className="flex gap-6">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={onlyHome}
              onChange={e => { setOnlyHome(e.target.checked); if (e.target.checked) setOnlyAway(false) }}
              className="accent-blue-600"
            />
            Solo in casa
          </label>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={onlyAway}
              onChange={e => { setOnlyAway(e.target.checked); if (e.target.checked) setOnlyHome(false) }}
              className="accent-blue-600"
            />
            Solo in trasferta
          </label>
        </div>

        {/* Team 2 */}
        <div>
          <label className="block text-sm font-medium mb-1">Squadra avversaria <span className="text-gray-400 font-normal">(opzionale)</span></label>
          <input
            type="text"
            value={teamTwo}
            onChange={e => setTeamTwo(e.target.value)}
            placeholder="es. Milano"
            className="border border-gray-300 rounded px-3 py-2 w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <button
          type="submit"
          className="bg-blue-700 hover:bg-blue-800 text-white font-semibold px-6 py-2 rounded"
        >
          Cerca
        </button>
      </form>
    </div>
  )
}
