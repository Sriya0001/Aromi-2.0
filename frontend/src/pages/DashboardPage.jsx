import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Sparkles, Dumbbell, MessageCircle, TrendingUp, Target, Heart, ArrowRight, Flame, Calendar as CalendarIcon } from 'lucide-react'
import Navbar from '../components/Navbar'
import useStore from '../store/useStore'
import { progressAPI, workoutAPI, nutritionAPI, calendarAPI } from '../services/api'
import toast from 'react-hot-toast'

const quickActions = [
    { icon: Heart, color: 'icon-green', label: 'Start Health Assessment', sub: 'Get AI-powered personalized plans', link: '/assessment', cta: 'Get Started →' },
    { icon: MessageCircle, color: 'icon-purple', label: 'Ask AROMI Coach', sub: 'Chat with your health companion', link: null, cta: 'Connect Now →', isChat: true },
    { icon: TrendingUp, color: 'icon-cyan', label: 'Track Progress', sub: 'Log your daily fitness metrics', link: '/progress', cta: 'Log Now →' },
    { icon: Dumbbell, color: 'icon-blue', label: 'AI Fitness Coach', sub: 'Chat with your personal AI trainer', link: null, cta: 'Chat Now →', isChat: true },
]

export default function DashboardPage() {
    const navigate = useNavigate()
    const { user, stats, setStats, toggleChatOpen } = useStore()
    const [loadingPlan, setLoadingPlan] = useState(false)

    const handleGenerate = async () => {
        if (user?.assessment_completed !== 'yes') {
            toast.error('Please complete the health assessment first!')
            navigate('/assessment')
            return
        }
        setLoadingPlan(true)
        try {
            await workoutAPI.generate()
            await nutritionAPI.generate()
            toast.success('Your personalized plans are ready! 🌟')
            navigate('/workout')
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to generate plans.')
        } finally {
            setLoadingPlan(false)
        }
    }

    return (
        <div className="min-h-screen bg-mesh">
            <Navbar />
            <div className="max-w-7xl mx-auto px-6 py-8">
                {/* Header */}
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
                    <h1 className="text-3xl font-bold text-main">
                        Welcome back, <span className="gradient-text">{user?.username}!</span>
                    </h1>
                    <p className="text-muted mt-1">Ready to continue your fitness journey? Let's make today count! 💪</p>
                </motion.div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Left: Quick Actions */}
                    <div className="lg:col-span-2 space-y-6">
                        <div>
                            <h2 className="text-lg font-semibold text-main mb-4 flex items-center gap-2">
                                <Sparkles size={18} className="text-purple-400" /> Quick Actions
                            </h2>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                {quickActions.map((action, i) => {
                                    const Icon = action.icon
                                    return (
                                        <motion.div
                                            key={i}
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ delay: i * 0.1 }}
                                            className="glass-card p-5 cursor-pointer"
                                            onClick={() => {
                                                if (action.isChat) toggleChatOpen()
                                                else if (action.link) navigate(action.link)
                                            }}
                                        >
                                            <div className={`w-12 h-12 rounded-xl ${action.color} flex items-center justify-center mb-3`}>
                                                <Icon size={22} className="text-white" />
                                            </div>
                                            <h3 className="text-white font-semibold mb-1">{action.label}</h3>
                                            <p className="text-slate-500 text-sm mb-3">{action.sub}</p>
                                            <span className="text-purple-400 text-sm font-medium">{action.cta}</span>
                                        </motion.div>
                                    )
                                })}
                            </div>
                        </div>

                        {/* Generate Plan Button */}
                        {user?.assessment_completed === 'yes' && (
                            <motion.button
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 0.5 }}
                                onClick={handleGenerate}
                                disabled={loadingPlan}
                                className="btn-primary w-full justify-center py-4 rounded-2xl disabled:opacity-60"
                            >
                                {loadingPlan ? (
                                    <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Generating your plans...</>
                                ) : (
                                    <><Sparkles size={18} /> Regenerate My Plans</>
                                )}
                            </motion.button>
                        )}
                    </div>

                    {/* Right: Sidebar */}
                    <div className="lg:col-span-1 space-y-6">
                        {/* Schedule Card */}
                        <div className="glass-card p-6">
                            <h3 className="text-main font-bold mb-4 flex items-center gap-2">
                                <CalendarIcon size={20} className="text-purple-400" /> My Schedule
                            </h3>
                            <p className="text-muted text-sm mb-6">View your personalized 7-day workout and nutrition plan.</p>
                            <button
                                onClick={() => navigate('/calendar')}
                                className="w-full py-4 rounded-2xl bg-purple-500 text-white font-bold text-lg hover:bg-purple-600 shadow-lg shadow-purple-500/20 active:scale-[0.98] transition-all flex items-center justify-center gap-2"
                            >
                                View Schedule →
                            </button>
                        </div>

                        {/* Charity Impact */}
                        <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.3 }}
                            className="glass-card p-6"
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-white font-semibold flex items-center gap-2">
                                    <Heart size={16} className="text-pink-400" /> Charity Impact 💝
                                </h3>
                                <div className="text-xl">🏅</div>
                            </div>

                            <div className="glass p-4 rounded-xl mb-4 text-center">
                                <p className="text-slate-400 text-xs mb-1">Impact Created</p>
                                <p className="text-2xl font-bold text-white">₹{stats?.charity_amount_inr || 0}</p>
                                <p className="text-[10px] text-slate-500 mt-1">via your healthy choices</p>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                {[
                                    { label: 'People Impacted', value: stats.people_impacted },
                                    { label: 'Calories Burned', value: Math.round(stats.total_calories_burned) },
                                    { label: 'Workouts Done', value: stats.total_workouts },
                                    { label: 'Healthy Meals', value: stats.total_healthy_meals },
                                ].map((s, i) => (
                                    <div key={i} className="glass p-3 rounded-xl text-center">
                                        <p className="text-xl font-bold text-purple-400">{s.value}</p>
                                        <p className="text-slate-500 text-xs mt-0.5">{s.label}</p>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-4 text-xs text-slate-600 text-center">
                                Workouts ₹2 each • Healthy Meals ₹1 each
                            </div>

                            {/* Streak */}
                            <div className="mt-4 p-3 glass rounded-xl flex items-center justify-between">
                                <div>
                                    <p className="text-white font-semibold text-sm flex items-center gap-1">
                                        <Flame size={14} className="text-orange-400" /> Streak
                                    </p>
                                    <p className="text-2xl font-bold gradient-text">{stats.streak_days}</p>
                                    <p className="text-slate-500 text-xs">days</p>
                                </div>
                                <div className="text-4xl">🔥</div>
                            </div>

                        </motion.div>
                    </div>
                </div>


            </div>
        </div>
    )
}

