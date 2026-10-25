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
    <div className="max-w-md mx-auto pt-10">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">LegaBasket Serie A Reference</h1>
        <p className="text-slate-500 dark:text-slate-400 mt-1 text-sm">Statistiche storiche delle partite</p>
      </div>

      <div className="bg-white dark:bg-slate-800 rounded-xl shadow-sm ring-1 ring-slate-200 dark:ring-slate-700 p-6">
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {/* Stagione */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">Stagione</label>
            <select
              value={season}
              onChange={e => setSeason(e.target.value)}
              className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm bg-white dark:bg-slate-700 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-slate-900 dark:focus:ring-slate-400 transition"
            >
              <option value="All">Tutte le stagioni</option>
              {seasons.map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

          {/* Team 1 */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">Squadra</label>
            <input
              type="text"
              value={team}
              onChange={e => setTeam(e.target.value)}
              placeholder="es. Varese"
              className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm bg-white dark:bg-slate-700 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-900 dark:focus:ring-slate-400 transition"
            />
          </div>

          {/* Checkboxes */}
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
              <input
                type="checkbox"
                checked={onlyHome}
                onChange={e => { setOnlyHome(e.target.checked); if (e.target.checked) setOnlyAway(false) }}
                className="accent-slate-900 dark:accent-orange-500"
              />
              <span className="text-slate-700 dark:text-slate-300">Solo in casa</span>
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer select-none">
              <input
                type="checkbox"
                checked={onlyAway}
                onChange={e => { setOnlyAway(e.target.checked); if (e.target.checked) setOnlyHome(false) }}
                className="accent-slate-900 dark:accent-orange-500"
              />
              <span className="text-slate-700 dark:text-slate-300">Solo in trasferta</span>
            </label>
          </div>

          {/* Team 2 */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-1.5">
              Squadra avversaria <span className="text-slate-400 dark:text-slate-500 font-normal normal-case">(opzionale)</span>
            </label>
            <input
              type="text"
              value={teamTwo}
              onChange={e => setTeamTwo(e.target.value)}
              placeholder="es. Milano"
              className="w-full border border-slate-300 dark:border-slate-600 rounded-lg px-3 py-2.5 text-sm bg-white dark:bg-slate-700 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-slate-900 dark:focus:ring-slate-400 transition"
            />
          </div>

          <button
            type="submit"
            className="w-full bg-slate-900 hover:bg-slate-700 dark:bg-orange-600 dark:hover:bg-orange-500 text-white font-semibold py-2.5 rounded-lg text-sm transition-colors mt-1"
          >
            Cerca partite
          </button>
        </form>
      </div>
    </div>
  )
}