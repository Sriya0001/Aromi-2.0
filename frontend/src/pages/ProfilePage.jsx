import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Save, User, Trophy, Award, Target, Flame, Calendar, Info, Heart } from 'lucide-react'
import Navbar from '../components/Navbar'
import { authAPI, progressAPI, reviewAPI, favouriteAPI } from '../services/api'
import useStore from '../store/useStore'
import { Send, Star } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ProfilePage() {
    const { user, setUser, stats, setStats } = useStore()
    const [activeTab, setActiveTab] = useState('details') // 'details', 'achievements', 'stories', or 'favourites'
    const [form, setForm] = useState({
        age: user?.age || '',
        gender: user?.gender || '',
        height: user?.height || '',
        weight: user?.weight || '',
        fitness_level: user?.fitness_level || '',
        fitness_goal: user?.fitness_goal || '',
        workout_preference: user?.workout_preference || '',
        diet_preference: user?.diet_preference || '',
        allergies: user?.allergies || '',
        medical_history: user?.medical_history || '',
    })
    const [saving, setSaving] = useState(false)
    const [reviewForm, setReviewForm] = useState({ name: user?.username || '', role: user?.role || '', text: '', rating: 5, emoji: user?.gender === 'female' ? '👩' : '👤' })
    const [submittingReview, setSubmittingReview] = useState(false)
    const [favs, setFavs] = useState([])
    const [loadingFavs, setLoadingFavs] = useState(false)

    useEffect(() => {
        progressAPI.getStats().then(res => setStats(res.data))
        fetchFavs()
    }, [])

    const fetchFavs = async () => {
        setLoadingFavs(true)
        try {
            const { data } = await favouriteAPI.getAll()
            setFavs(data)
        } finally {
            setLoadingFavs(false)
        }
    }

    const handleSave = async (e) => {
        // ... (existing handleSave logic)
        e.preventDefault()
        setSaving(true)
        try {
            await authAPI.updateProfile({
                ...form,
                age: parseInt(form.age) || null,
                height: parseInt(form.height) || null,
                weight: parseInt(form.weight) || null,
            })
            const { data } = await authAPI.getMe()
            setUser(data)
            toast.success('Profile updated! 🎉')
        } catch {
            toast.error('Failed to update profile')
        } finally {
            setSaving(false)
        }
    }

    const handleSubmitReview = async (e) => {
        e.preventDefault()
        setSubmittingReview(true)
        try {
            await reviewAPI.create(reviewForm)
            toast.success('Thank you for sharing your story! ❤️')
            setReviewForm({ ...reviewForm, text: '', rating: 5 })
        } catch {
            toast.error('Failed to submit review')
        } finally {
            setSubmittingReview(false)
        }
    }

    const achievements = [
        { id: 'first_step', name: 'First Step', icon: '🏃', desc: 'Complete your first workout', target: 1, current: stats.total_workouts, pts: 10 },
        { id: 'workout_warrior', name: 'Workout Warrior', icon: '💪', desc: 'Complete 5 workouts', target: 5, current: stats.total_workouts, pts: 25 },
        { id: 'beast_mode', name: 'Beast Mode', icon: '🦍', desc: 'Complete 10 workouts', target: 10, current: stats.total_workouts, pts: 50 },
        { id: 'nutrition_ninja', name: 'Nutrition Ninja', icon: '🥗', desc: 'Track 5 healthy meals', target: 5, current: stats.total_healthy_meals, pts: 20 },
        { id: 'fire_starter', name: 'Fire Starter', icon: '🔥', desc: 'Burn 500 total calories', target: 500, current: stats.total_calories_burned, pts: 15 },
        { id: 'fire_master', name: 'Fire Master', icon: '🔥🔥', desc: 'Burn 1000 total calories', target: 1000, current: stats.total_calories_burned, pts: 40 },
        { id: 'consistency', name: 'Consistency Counts', icon: '📅', desc: 'Achieve a 3-day streak', target: 3, current: stats.streak_days, pts: 30 },
        { id: 'streak_king', name: 'Streak King', icon: '👑', desc: 'Achieve a 7-day streak', target: 7, current: stats.streak_days, pts: 60 },
    ]

    const unlockedCount = achievements.filter(a => a.current >= a.target).length
    const overallProgress = Math.round((unlockedCount / achievements.length) * 100)

    const fields = [
        { key: 'age', label: 'Age', type: 'number', placeholder: '25' },
        { key: 'gender', label: 'Gender', type: 'select', options: ['Male', 'Female', 'Other'] },
        { key: 'height', label: 'Height (cm)', type: 'number', placeholder: '170' },
        { key: 'weight', label: 'Weight (kg)', type: 'number', placeholder: '70' },
        { key: 'fitness_level', label: 'Fitness Level', type: 'select', options: ['beginner', 'intermediate', 'advanced'] },
        { key: 'fitness_goal', label: 'Fitness Goal', type: 'select', options: ['weight loss', 'muscle gain', 'general fitness', 'endurance', 'flexibility'] },
        { key: 'workout_preference', label: 'Workout Location', type: 'select', options: ['home', 'gym', 'outdoor', 'mixed'] },
        { key: 'diet_preference', label: 'Diet Preference', type: 'select', options: ['vegetarian', 'non-vegetarian', 'vegan', 'eggetarian'] },
        { key: 'allergies', label: 'Food Allergies', type: 'text', placeholder: 'None' },
        { key: 'medical_history', label: 'Medical History', type: 'text', placeholder: 'None' },
    ]

    return (
        <div className="min-h-screen bg-mesh">
            <Navbar />
            <div className="max-w-4xl mx-auto px-6 py-8">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-8">
                    <h1 className="text-3xl font-bold text-white mb-1">My Profile 👤</h1>
                    <p className="text-slate-400">Update your details and track your milestones</p>
                </motion.div>

                {/* Avatar Header */}
                <div className="glass-card p-6 flex flex-col md:flex-row items-center justify-between gap-5 mb-6">
                    <div className="flex items-center gap-5 w-full">
                        <div className="w-16 h-16 rounded-2xl icon-purple flex items-center justify-center text-3xl">
                            {user?.gender === 'female' ? '👩' : '👤'}
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">{user?.username}</h2>
                            <p className="text-slate-400 text-sm">{user?.email}</p>
                            <div className="flex gap-2 mt-2">
                                <span className="px-2 py-0.5 rounded-lg bg-purple-500/20 text-purple-400 text-xs font-medium capitalize">{user?.fitness_level || 'beginner'}</span>
                                <span className="px-2 py-0.5 rounded-lg bg-cyan-500/20 text-cyan-400 text-xs font-medium capitalize">{user?.fitness_goal || 'general fitness'}</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex bg-slate-800/50 p-1 rounded-xl w-full md:w-auto">
                        <button onClick={() => setActiveTab('details')}
                            className={`flex-1 md:flex-none px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'details' ? 'bg-purple-500 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}>
                            Account
                        </button>
                        <button onClick={() => setActiveTab('achievements')}
                            className={`flex-1 md:flex-none px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'achievements' ? 'bg-purple-500 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}>
                            Achievements
                        </button>
                        <button onClick={() => setActiveTab('stories')}
                            className={`flex-1 md:flex-none px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'stories' ? 'bg-purple-500 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}>
                            My Story
                        </button>
                        <button onClick={() => setActiveTab('favourites')}
                            className={`flex-1 md:flex-none px-4 py-2 rounded-lg text-sm font-medium transition-all ${activeTab === 'favourites' ? 'bg-purple-500 text-white shadow-lg' : 'text-slate-400 hover:text-white'}`}>
                            Favourites
                        </button>
                    </div>
                </div>

                <AnimatePresence mode="wait">
                    {activeTab === 'details' ? (
                        <motion.div key="details" initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 20 }}>
                            <form onSubmit={handleSave} className="glass-card p-6">
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                                    {fields.map(f => (
                                        <div key={f.key}>
                                            <label className="block text-sm font-medium text-slate-300 mb-2">{f.label}</label>
                                            {f.type === 'select' ? (
                                                <select className="input-dark" value={form[f.key]} onChange={e => setForm({ ...form, [f.key]: e.target.value })}>
                                                    <option value="">Select...</option>
                                                    {f.options.map(o => <option key={o} value={o}>{o.charAt(0).toUpperCase() + o.slice(1)}</option>)}
                                                </select>
                                            ) : (
                                                <input type={f.type} className="input-dark" placeholder={f.placeholder}
                                                    value={form[f.key]} onChange={e => setForm({ ...form, [f.key]: e.target.value })} />
                                            )}
                                        </div>
                                    ))}
                                </div>

                                <motion.button type="submit" disabled={saving} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                                    className="btn-primary mt-6 px-8 py-3 disabled:opacity-60">
                                    {saving ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Saving...</> : <><Save size={16} /> Save Changes</>}
                                </motion.button>
                            </form>
                        </motion.div>
                    ) : activeTab === 'achievements' ? (
                        <motion.div key="achievements" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-6">
                            {/* ... (achievements content remains same) */}
                            <div className="glass-card p-6 border-l-4 border-purple-500">
                                <div className="flex items-center justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-xl bg-purple-500/20 flex items-center justify-center text-purple-400">
                                            <Trophy size={20} />
                                        </div>
                                        <div>
                                            <h3 className="text-white font-bold">Achievement Progress</h3>
                                            <p className="text-slate-500 text-xs">Keep pushing your limits!</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <span className="text-2xl font-black text-white">{unlockedCount}</span>
                                        <span className="text-slate-500 text-sm font-bold">/{achievements.length}</span>
                                        <p className="text-[10px] text-slate-500 uppercase tracking-wider font-bold">Unlocked</p>
                                    </div>
                                </div>
                                <div className="w-full bg-slate-800 rounded-full h-2 mb-2">
                                    <motion.div initial={{ width: 0 }} animate={{ width: `${overallProgress}%` }}
                                        className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full" />
                                </div>
                                <div className="flex justify-between text-[10px] text-slate-500 font-bold uppercase">
                                    <span>Overall Completion</span>
                                    <span>{overallProgress}%</span>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {achievements.map((item, i) => {
                                    const isUnlocked = item.current >= item.target
                                    const progress = Math.min(100, Math.round((item.current / item.target) * 100))

                                    return (
                                        <motion.div key={item.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                                            className={`glass-card p-5 relative overflow-hidden group ${isUnlocked ? 'border-purple-500/50 bg-purple-500/5' : 'opacity-60 grayscale'}`}>

                                            {isUnlocked && (
                                                <div className="absolute top-3 right-3 px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-400 text-[10px] font-bold uppercase tracking-wider">
                                                    +{item.pts} pts
                                                </div>
                                            )}

                                            <div className="flex items-start gap-4">
                                                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center text-2xl bg-slate-800/80 shadow-inner block shrink-0 ${isUnlocked ? 'icon-purple' : ''}`}>
                                                    {item.icon}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <h4 className="text-white font-bold mb-0.5 truncate">{item.name}</h4>
                                                    <p className="text-slate-500 text-xs mb-3 leading-relaxed">{item.desc}</p>

                                                    <div className="space-y-1.5">
                                                        <div className="flex justify-between text-[10px] text-slate-400 font-medium">
                                                            <span>Progress</span>
                                                            <span className={isUnlocked ? 'text-purple-400' : ''}>{progress}%</span>
                                                        </div>
                                                        <div className="w-full bg-slate-800/50 rounded-full h-1.5 overflow-hidden">
                                                            <motion.div initial={{ width: 0 }} animate={{ width: `${progress}%` }}
                                                                className={`h-full rounded-full ${isUnlocked ? 'bg-purple-500' : 'bg-slate-600'}`} />
                                                        </div>
                                                        <p className="text-[10px] text-slate-500 text-right">{isUnlocked ? '100% complete' : `${progress}% complete`}</p>
                                                    </div>
                                                </div>
                                            </div>
                                        </motion.div>
                                    )
                                })}
                            </div>
                        </motion.div>
                    ) : activeTab === 'stories' ? (
                        <motion.div key="stories" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }}>
                            <div className="glass-card p-8 max-w-2xl mx-auto">
                                <h3 className="text-xl font-bold text-white mb-6">Share Your Story 🌟</h3>
                                <p className="text-slate-400 text-sm mb-8">Tell us about your fitness journey with ArogyaMitra. Your review will inspire others in the community!</p>

                                <form onSubmit={handleSubmitReview} className="space-y-6">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-2">Display Name</label>
                                            <input type="text" required className="input-dark" value={reviewForm.name} onChange={e => setReviewForm({ ...reviewForm, name: e.target.value })} />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-slate-300 mb-2">Your Role (Optional)</label>
                                            <input type="text" className="input-dark" placeholder="e.g., Software Engineer" value={reviewForm.role} onChange={e => setReviewForm({ ...reviewForm, role: e.target.value })} />
                                        </div>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-300 mb-2">Your Thoughts</label>
                                        <textarea required rows="4" className="input-dark" placeholder="How has ArogyaMitra helped you?" value={reviewForm.text} onChange={e => setReviewForm({ ...reviewForm, text: e.target.value })}></textarea>
                                    </div>
                                    <div className="flex items-center justify-between pt-4">
                                        <div className="flex gap-2">
                                            {[1, 2, 3, 4, 5].map(s => (
                                                <button key={s} type="button" onClick={() => setReviewForm({ ...reviewForm, rating: s })}
                                                    className={`transition-all ${reviewForm.rating >= s ? 'text-yellow-400 scale-110' : 'text-slate-600'}`}>
                                                    <Star size={24} fill={reviewForm.rating >= s ? "currentColor" : "none"} />
                                                </button>
                                            ))}
                                        </div>
                                        <motion.button type="submit" disabled={submittingReview} whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
                                            className="btn-primary px-8 py-3 rounded-xl flex items-center gap-2 text-white">
                                            {submittingReview ? 'Submitting...' : <><Send size={16} /> Submit Story</>}
                                        </motion.button>
                                    </div>
                                </form>
                            </div>
                        </motion.div>
                    ) : (
                        <motion.div key="favourites" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="text-white font-bold text-lg">Favourite Workouts ❤️</h3>
                                <button onClick={fetchFavs} className="text-xs text-purple-400 hover:text-purple-300 font-bold uppercase tracking-wider">Refresh</button>
                            </div>

                            {loadingFavs ? (
                                <div className="text-center py-12 text-slate-500">Loading favourites...</div>
                            ) : favs.length === 0 ? (
                                <div className="glass-card p-12 text-center">
                                    <div className="text-4xl mb-4">💝</div>
                                    <p className="text-slate-400">No favourite workouts yet. Go to the workout page and click the heart icon to save one!</p>
                                </div>
                            ) : (
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {favs.map(f => (
                                        <motion.div key={f.id} layout className="glass-card p-5 group relative">
                                            <button
                                                onClick={async () => {
                                                    await favouriteAPI.remove(f.id);
                                                    setFavs(favs.filter(x => x.id !== f.id));
                                                    toast.success('Removed from favourites');
                                                }}
                                                className="absolute top-4 right-4 text-red-500/40 group-hover:text-red-500 transition-all"
                                            >
                                                <Heart size={20} fill="currentColor" />
                                            </button>

                                            <div className="flex items-center gap-3 mb-4">
                                                <div className="w-10 h-10 rounded-xl icon-purple flex items-center justify-center text-xl">💪</div>
                                                <div>
                                                    <h4 className="text-white font-bold leading-tight">{f.name}</h4>
                                                    <p className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">{f.muscle_group || 'General'}</p>
                                                </div>
                                            </div>

                                            <div className="space-y-2 mb-4">
                                                <div className="flex justify-between text-xs">
                                                    <span className="text-slate-300">Sets & Reps</span>
                                                    <span className="text-slate-500 font-medium">{f.sets} × {f.reps}</span>
                                                </div>
                                                <div className="flex justify-between text-xs">
                                                    <span className="text-slate-300">Rest Time</span>
                                                    <span className="text-slate-500 font-medium">{f.rest_seconds}s</span>
                                                </div>
                                                {f.instructions && (
                                                    <p className="text-[10px] text-slate-500 leading-relaxed line-clamp-2 mt-2 italic">"{f.instructions}"</p>
                                                )}
                                            </div>

                                            <div className="flex items-center justify-between pt-4 border-t border-slate-800/50">
                                                {f.video_url ? (
                                                    <a href={f.video_url} target="_blank" rel="noreferrer" className="text-red-400 text-[10px] font-black uppercase tracking-widest hover:text-red-300">Watch Video</a>
                                                ) : (
                                                    <span className="text-slate-600 text-[10px] uppercase font-bold">No Video</span>
                                                )}
                                            </div>
                                        </motion.div>
                                    ))}
                                </div>
                            )}
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    )
}

