import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Calendar as CalendarIcon, Dumbbell, Apple, ChevronLeft, ChevronRight, Clock } from 'lucide-react'
import Navbar from '../components/Navbar'
import { workoutAPI, nutritionAPI } from '../services/api'
import { useNavigate } from 'react-router-dom'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
const MEAL_EMOJIS = { breakfast: '🌅', lunch: '☀️', dinner: '🌙', mid_morning_snack: '🍎', evening_snack: '🍵' }

export default function CalendarPage() {
    const navigate = useNavigate()
    const [workoutPlan, setWorkoutPlan] = useState([])
    const [nutritionPlan, setNutritionPlan] = useState([])
    const [loading, setLoading] = useState(true)
    const [selectedDay, setSelectedDay] = useState(new Date().getDay() || 7)

    useEffect(() => {
        Promise.all([workoutAPI.getPlan(), nutritionAPI.getPlan()])
            .then(([wRes, nRes]) => {
                setWorkoutPlan(wRes.data.plan || [])
                setNutritionPlan(nRes.data.plan || [])
                setLoading(false)
            })
            .catch(() => setLoading(false))
    }, [])

    const getDayData = (dayNum) => {
        const workout = workoutPlan.find(p => p.day === dayNum)
        const nutrition = nutritionPlan.find(p => p.day === dayNum)
        return { workout, nutrition }
    }

    if (loading) return (
        <div className="min-h-screen bg-mesh"><Navbar />
            <div className="flex items-center justify-center h-[60vh]">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
                    <p className="text-slate-400">Loading your schedule...</p>
                </div>
            </div>
        </div>
    )

    const activeDayData = getDayData(selectedDay)

    return (
        <div className="min-h-screen bg-mesh">
            <Navbar />
            <div className="max-w-7xl mx-auto px-6 py-8">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-1">Weekly Schedule 📅</h1>
                        <p className="text-slate-400">Your 7-day personalized workout and nutrition roadmap</p>
                    </div>
                    <button onClick={() => navigate('/dashboard')} className="text-slate-400 hover:text-white transition-colors text-sm flex items-center gap-1">
                        <ChevronLeft size={16} /> Back to Dashboard
                    </button>
                </motion.div>

                {/* Day Selection Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-8">
                    {DAYS.map((day, i) => {
                        const dayNum = i + 1
                        const data = getDayData(dayNum)
                        return (
                            <motion.button
                                key={day}
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => setSelectedDay(dayNum)}
                                className={`p-4 rounded-2xl border-2 text-left transition-all ${selectedDay === dayNum
                                    ? 'border-purple-500 bg-purple-500/10 shadow-lg shadow-purple-500/10'
                                    : 'border-white/5 bg-white/5 hover:border-white/10'}`}
                            >
                                <p className={`text-xs font-bold mb-1 ${selectedDay === dayNum ? 'text-purple-400' : 'text-slate-500'}`}>
                                    {day.toUpperCase()}
                                </p>
                                <div className="flex gap-1.5 mt-2">
                                    {data.workout && <div className="w-2 h-2 rounded-full bg-orange-400" title="Workout scheduled" />}
                                    {data.nutrition && <div className="w-2 h-2 rounded-full bg-green-400" title="Meals planned" />}
                                </div>
                            </motion.button>
                        )
                    })}
                </div>

                {/* Day Detail View */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    {/* Main Content */}
                    <div className="lg:col-span-8 space-y-6">
                        {/* Workout Summary */}
                        <motion.div
                            key={`w-${selectedDay}`}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="glass-card p-6"
                        >
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl icon-purple flex items-center justify-center text-white">
                                        <Dumbbell size={20} />
                                    </div>
                                    <h2 className="text-xl font-bold text-white">Workout Session</h2>
                                </div>
                                <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-400 text-xs font-semibold">
                                    {activeDayData.workout?.duration_minutes || 45} MINS
                                </span>
                            </div>

                            {activeDayData.workout ? (
                                <div>
                                    <p className="text-white font-semibold text-lg mb-2">{activeDayData.workout.day_name}: {activeDayData.workout.focus}</p>
                                    <p className="text-slate-400 text-sm mb-6 pb-6 border-b border-white/5 leading-relaxed">
                                        {activeDayData.workout.warmup}
                                    </p>

                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {activeDayData.workout.exercises?.slice(0, 4).map((ex, idx) => (
                                            <div key={idx} className="flex items-center gap-3 p-3 rounded-xl bg-white/5 border border-white/5">
                                                <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center text-xs font-bold text-slate-400">
                                                    {idx + 1}
                                                </div>
                                                <div>
                                                    <p className="text-white text-sm font-medium">{ex.name}</p>
                                                    <p className="text-slate-500 text-[10px]">{ex.sets} sets × {ex.reps} reps</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    <button
                                        onClick={() => navigate('/workout')}
                                        className="mt-6 w-full py-3 rounded-xl bg-purple-500 text-white font-bold text-sm hover:bg-purple-600 transition-all"
                                    >
                                        Start This Workout 💪
                                    </button>
                                </div>
                            ) : (
                                <div className="py-8 text-center">
                                    <p className="text-slate-500 italic">No workout planned for this day.</p>
                                </div>
                            )}
                        </motion.div>

                        {/* Nutrition Summary */}
                        <motion.div
                            key={`n-${selectedDay}`}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.1 }}
                            className="glass-card p-6"
                        >
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-xl icon-green flex items-center justify-center text-white">
                                        <Apple size={20} />
                                    </div>
                                    <h2 className="text-xl font-bold text-white">Meals & Nutrition</h2>
                                </div>
                                <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-semibold uppercase">
                                    {activeDayData.nutrition?.calories || 0} KCAL
                                </span>
                            </div>

                            {activeDayData.nutrition ? (
                                <div className="space-y-4">
                                    {Object.entries(activeDayData.nutrition.meals || {}).map(([type, meal]) => (
                                        <div key={type} className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5 group hover:border-green-500/30 transition-all">
                                            <div className="flex items-center gap-4">
                                                <span className="text-2xl">{MEAL_EMOJIS[type] || '🍽️'}</span>
                                                <div>
                                                    <p className="text-slate-500 text-xs capitalize">{type.replace(/_/g, ' ')}</p>
                                                    <p className="text-white font-medium group-hover:text-green-400 transition-colors">{meal.name || meal}</p>
                                                </div>
                                            </div>
                                            <Clock size={16} className="text-slate-600" />
                                        </div>
                                    ))}

                                    <button
                                        onClick={() => navigate('/nutrition')}
                                        className="mt-4 w-full py-3 rounded-xl bg-green-500/10 border border-green-500/30 text-green-400 font-bold text-sm hover:bg-green-500/20 transition-all"
                                    >
                                        View Full Recipes 🥗
                                    </button>
                                </div>
                            ) : (
                                <div className="py-8 text-center">
                                    <p className="text-slate-500 italic">No nutrition plan for this day.</p>
                                </div>
                            )}
                        </motion.div>
                    </div>

                    {/* Sidebar Stats */}
                    <div className="lg:col-span-4 space-y-6">
                        <div className="glass-card p-6">
                            <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                                <CalendarIcon size={18} className="text-purple-400" />
                                Weekly Overview
                            </h3>
                            <div className="space-y-4">
                                <div className="p-4 rounded-xl bg-white/5">
                                    <p className="text-slate-500 text-xs mb-1">Total Workouts</p>
                                    <p className="text-2xl font-bold text-white">{workoutPlan.length} sessions</p>
                                </div>
                                <div className="p-4 rounded-xl bg-white/5">
                                    <p className="text-slate-500 text-xs mb-1">Avg. Daily Calories</p>
                                    <p className="text-2xl font-bold text-white">
                                        {Math.round(nutritionPlan.reduce((acc, curr) => acc + (curr.calories || 0), 0) / (nutritionPlan.length || 1))} kcal
                                    </p>
                                </div>
                                <div className="p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
                                    <p className="text-purple-400 text-xs font-bold mb-2 uppercase tracking-wider">Aromi Tip 🤖</p>
                                    <p className="text-slate-300 text-sm leading-relaxed">
                                        "Consistency is key! Try to stick to your Workout and Meal times to see the best results from your personalized plan."
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
