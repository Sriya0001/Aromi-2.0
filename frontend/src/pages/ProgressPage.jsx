import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import Navbar from '../components/Navbar'
import { progressAPI } from '../services/api'
import useStore from '../store/useStore'
import toast from 'react-hot-toast'

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload?.length) return (
        <div className="glass p-3 rounded-xl">
            <p className="text-slate-400 text-xs mb-1">{label}</p>
            {payload.map((p, i) => <p key={i} className="text-white text-sm font-medium">{p.name}: <span style={{ color: p.color }}>{p.value}</span></p>)}
        </div>
    )
    return null
}

export default function ProgressPage() {
    const [history, setHistory] = useState([])
    const { stats, setStats } = useStore()
    const [logForm, setLogForm] = useState({ weight: '', calories_burned: '', healthy_meals: '', notes: '' })
    const [logging, setLogging] = useState(false)

    useEffect(() => {
        Promise.all([progressAPI.getHistory(), progressAPI.getStats()])
            .then(([h, s]) => {
                setHistory([...(h.data || [])].reverse().slice(-14))
                setStats(s.data)
            })
    }, [])

    const handleLog = async (e) => {
        e.preventDefault()
        setLogging(true)
        try {
            await progressAPI.log({
                weight: logForm.weight ? parseFloat(logForm.weight) : null,
                calories_burned: parseFloat(logForm.calories_burned) || 0,
                healthy_meals: parseInt(logForm.healthy_meals) || 0,
                notes: logForm.notes,
            })
            const [h, s] = await Promise.all([progressAPI.getHistory(), progressAPI.getStats()])
            setHistory([...(h.data || [])].reverse().slice(-14))
            setStats(s.data)
            setLogForm({ weight: '', calories_burned: '', healthy_meals: '', notes: '' })
            toast.success('Progress logged! Keep it up! 💪')
        } catch {
            toast.error('Failed to log progress')
        } finally {
            setLogging(false)
        }
    }

    const chartData = history.map(r => ({
        date: r.date?.slice(5) || '',
        calories: Math.round(r.calories_burned),
        weight: r.weight || null,
        workouts: r.workouts_completed,
    }))

    const statCards = [
        { label: 'Total Calories Burned', value: Math.round(stats.total_calories_burned), color: 'text-orange-400', emoji: '🔥' },
        { label: 'Total Workouts', value: stats.total_workouts, color: 'text-purple-400', emoji: '🏋️' },
        { label: 'Healthy Meals', value: stats.total_healthy_meals, color: 'text-green-400', emoji: '🥗' },
        { label: 'Day Streak', value: stats.streak_days, color: 'text-yellow-400', emoji: '⚡' },
        { label: 'Charity Impact', value: `₹${stats.charity_amount_inr}`, color: 'text-pink-400', emoji: '❤️' },
        { label: 'Lives Impacted', value: stats.people_impacted, color: 'text-cyan-400', emoji: '🌍' },
    ]

    return (
        <div className="min-h-screen bg-mesh">
            <Navbar />
            <div className="max-w-6xl mx-auto px-6 py-8">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
                    <h1 className="text-3xl font-bold text-white mb-1">Progress Tracker 📊</h1>
                    <p className="text-slate-400">Track your fitness journey and watch yourself transform</p>
                </motion.div>

                {/* Stat Cards */}
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
                    {statCards.map((s, i) => (
                        <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.07 }} className="glass-card p-4 text-center">
                            <div className="text-2xl mb-2">{s.emoji}</div>
                            <div className={`text-xl font-bold ${s.color}`}>{s.value}</div>
                            <div className="text-slate-500 text-xs mt-1">{s.label}</div>
                        </motion.div>
                    ))}
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Charts */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Calories Chart */}
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="glass-card p-6">
                            <h3 className="text-white font-semibold mb-4">🔥 Calories Burned (Last 14 days)</h3>
                            {chartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={200}>
                                    <AreaChart data={chartData}>
                                        <defs>
                                            <linearGradient id="calorieGrad" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.4} />
                                                <stop offset="95%" stopColor="#7c3aed" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e3f" />
                                        <XAxis dataKey="date" stroke="#475569" tick={{ fontSize: 10 }} />
                                        <YAxis stroke="#475569" tick={{ fontSize: 10 }} />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Area type="monotone" dataKey="calories" stroke="#7c3aed" fill="url(#calorieGrad)" strokeWidth={2} name="Calories" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            ) : <p className="text-slate-500 text-center py-8">Log workouts to see your progress chart</p>}
                        </motion.div>

                        {/* Workouts Chart */}
                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="glass-card p-6">
                            <h3 className="text-white font-semibold mb-4">🏋️ Workout Frequency</h3>
                            {chartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height={150}>
                                    <BarChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1e1e3f" />
                                        <XAxis dataKey="date" stroke="#475569" tick={{ fontSize: 10 }} />
                                        <YAxis stroke="#475569" tick={{ fontSize: 10 }} />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Bar dataKey="workouts" fill="#06b6d4" radius={[4, 4, 0, 0]} name="Workouts" />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : <p className="text-slate-500 text-center py-8">No workout data yet</p>}
                        </motion.div>
                    </div>

                    {/* Log Form */}
                    <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 }} className="glass-card p-6 h-fit">
                        <h3 className="text-white font-semibold mb-4">📝 Log Today's Progress</h3>
                        <form onSubmit={handleLog} className="space-y-4">
                            <div>
                                <label className="text-slate-400 text-sm block mb-1">Weight (kg)</label>
                                <input type="number" step="0.1" className="input-dark" placeholder="70.5"
                                    value={logForm.weight} onChange={e => setLogForm({ ...logForm, weight: e.target.value })} />
                            </div>
                            <div>
                                <label className="text-slate-400 text-sm block mb-1">Calories Burned</label>
                                <input type="number" className="input-dark" placeholder="300"
                                    value={logForm.calories_burned} onChange={e => setLogForm({ ...logForm, calories_burned: e.target.value })} />
                            </div>
                            <div>
                                <label className="text-slate-400 text-sm block mb-1">Healthy Meals</label>
                                <input type="number" className="input-dark" placeholder="3" min="0" max="6"
                                    value={logForm.healthy_meals} onChange={e => setLogForm({ ...logForm, healthy_meals: e.target.value })} />
                            </div>
                            <div>
                                <label className="text-slate-400 text-sm block mb-1">Notes</label>
                                <textarea className="input-dark h-20 resize-none" placeholder="How did today go?"
                                    value={logForm.notes} onChange={e => setLogForm({ ...logForm, notes: e.target.value })} />
                            </div>
                            <motion.button type="submit" disabled={logging} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                                className="btn-primary w-full justify-center py-3 disabled:opacity-60">
                                {logging ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Saving...</> : '💾 Log Progress'}
                            </motion.button>
                        </form>
                    </motion.div>
                </div>
            </div>
        </div>
    )
}
