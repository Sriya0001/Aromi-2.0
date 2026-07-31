import { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Play, Pause, CheckCircle, ChevronDown, ChevronUp, Youtube, Timer, Flame, Trophy, Heart } from 'lucide-react'
import Navbar from '../components/Navbar'
import { workoutAPI, progressAPI, authAPI, favouriteAPI } from '../services/api'
import { useNavigate, useLocation } from 'react-router-dom'
import toast from 'react-hot-toast'
import useStore from '../store/useStore'

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

function WorkoutTimer({ onComplete }) {
    const [seconds, setSeconds] = useState(0)
    const [running, setRunning] = useState(false)
    const intervalRef = useRef(null)

    useEffect(() => {
        if (running) {
            intervalRef.current = setInterval(() => setSeconds(s => s + 1), 1000)
        } else {
            clearInterval(intervalRef.current)
        }
        return () => clearInterval(intervalRef.current)
    }, [running])

    const fmt = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`

    return (
        <div className="glass-card p-4 flex items-center gap-4">
            <div className="text-3xl font-mono font-bold text-main">{fmt(seconds)}</div>
            <button onClick={() => setRunning(r => !r)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${running ? 'bg-red-500/20 text-red-400 border border-red-500/30' : 'bg-green-500/20 text-green-400 border border-green-500/30'}`}>
                {running ? <><Pause size={16} /> Pause</> : <><Play size={16} /> Start</>}
            </button>
            <button onClick={onComplete} className="px-4 py-2 rounded-lg bg-purple-500/20 text-purple-400 border border-purple-500/30 font-medium">
                <CheckCircle size={16} />
            </button>
        </div>
    )
}

const CURATED_VIDEOS = {
    "russian twist": "wkD8rjkodUI",
    "russian twists": "wkD8rjkodUI",
    "kettlebell": "YSxHifyI6s8",
    "kettlebell swings": "YSxHifyI6s8",
    "dumbbell swings": "YSxHifyI6s8",
    "swing": "YSxHifyI6s8",
    "swings": "YSxHifyI6s8",
    "incline push-up": "IODxDxX7oi4",
    "incline push-ups": "IODxDxX7oi4",
    "push-up": "IODxDxX7oi4",
    "push-ups": "IODxDxX7oi4",
    "pushup": "IODxDxX7oi4",
    "plank": "pSHjTRCQxIw",
    "plank hold": "pSHjTRCQxIw",
    "squat": "aclHkVaku9U",
    "squats": "aclHkVaku9U",
    "lunge": "QOVaHwm-Q6U",
    "lunges": "QOVaHwm-Q6U",
    "dumbbell chest flyes": "eozdVDA78K0",
    "step-ups": "dXxApOi17yY",
    "dead bug": "4XLEnwUr1d8",
    "jumping jacks": "iSSAk4Xo4GA",
    "mountain climbers": "zT-9L3CEcmk",
    "bicycle crunches": "9FGilxCbdz8",
    "crunches": "2pLT-ilgU6s",
    "crunch": "2pLT-ilgU6s",
    "glute bridge": "8bbE64NuDTU",
    "bench press": "rT7DgCr-3pg",
    "pull-ups": "eGo4IYlbE5g",
    "dumbbell rows": "roCP6wCXPqo",
    "bicep curls": "ykJmrZ5v0Oo",
    "tricep dips": "0326dy_-CzM",
    "shoulder press": "qEwKCR5JCog",
}

function getExerciseVideo(ex) {
    if (ex?.video?.video_id && !ex.video.url?.includes('results?search_query=')) {
        return {
            video_id: ex.video.video_id,
            url: ex.video.url || `https://www.youtube.com/watch?v=${ex.video.video_id}`
        }
    }
    const nameLower = (ex?.name || '').toLowerCase()
    let foundId = null
    for (const [key, id] of Object.entries(CURATED_VIDEOS)) {
        if (nameLower.includes(key) || key.includes(nameLower)) {
            foundId = id
            break
        }
    }
    if (!foundId) {
        if (nameLower.includes("twist")) foundId = "wkD8rjkodUI"
        else if (nameLower.includes("push")) foundId = "IODxDxX7oi4"
        else if (nameLower.includes("squat")) foundId = "aclHkVaku9U"
        else if (nameLower.includes("lunge")) foundId = "QOVaHwm-Q6U"
        else if (nameLower.includes("swing")) foundId = "YSxHifyI6s8"
        else if (nameLower.includes("row")) foundId = "roCP6wCXPqo"
        else if (nameLower.includes("press")) foundId = "qEwKCR5JCog"
        else if (nameLower.includes("curl")) foundId = "ykJmrZ5v0Oo"
        else if (nameLower.includes("dip")) foundId = "0326dy_-CzM"
        else foundId = "pSHjTRCQxIw"
    }

    return {
        video_id: foundId,
        url: `https://www.youtube.com/watch?v=${foundId}`
    }
}

export default function WorkoutPage() {
    const navigate = useNavigate()
    const [plan, setPlan] = useState([])
    const [selectedDay, setSelectedDay] = useState(new Date().getDay() || 7)
    const [expandedEx, setExpandedEx] = useState(null)
    const [videoEx, setVideoEx] = useState(null)
    const [loading, setLoading] = useState(true)
    const [completing, setCompleting] = useState(false)
    const [completionMsg, setCompletionMsg] = useState(null)
    const [generating, setGenerating] = useState(false)
    const [favourites, setFavourites] = useState([])
    const [isFavouriting, setIsFavouriting] = useState(false)

    const location = useLocation()
    const { user, setUser, workoutPlan, setWorkoutPlan, setStats } = useStore()

    useEffect(() => {
        setLoading(true)
        Promise.all([
            workoutAPI.getPlan(),
            favouriteAPI.getAll()
        ]).then(([workoutRes, favRes]) => {
            const fetchedPlan = workoutRes.data.plan || []
            setPlan(fetchedPlan)
            setWorkoutPlan(fetchedPlan)
            setFavourites(favRes.data || [])
            setLoading(false)
        }).catch(() => setLoading(false))
    }, [])

    // Re-sync local state when store is updated (e.g. by AROMI chat)
    useEffect(() => {
        if (workoutPlan && workoutPlan.length > 0) {
            setPlan([...workoutPlan]);
        }
    }, [workoutPlan])

    useEffect(() => {
        const params = new URLSearchParams(location.search)
        const dayParam = params.get('day')

        if (dayParam) {
            // Find day number by name
            const found = plan.find(p => p.day_name === dayParam);
            if (found) setSelectedDay(found.day);
        }
    }, [location, plan])

    const todayPlan = plan.find(p => p.day === selectedDay)

    const handleComplete = async () => {
        const exercises = todayPlan?.exercises || []
        const cals = todayPlan?.calories_estimate || exercises.length * 40
        const sets = exercises.reduce((a, e) => a + (parseInt(e.sets) || 3), 0)

        setCompleting(true)
        try {
            const { data } = await workoutAPI.completeWorkout(cals, sets, todayPlan?.duration_minutes || 45)
            await progressAPI.log({ calories_burned: cals, workouts_completed: 1, sets_completed: sets, workout_duration: todayPlan?.duration_minutes || 45 })
            setCompletionMsg({ message: data.message, calories: cals, sets })
            const statsRes = await progressAPI.getStats()
            setStats(statsRes.data)
        } catch (err) {
            toast.error('Failed to log workout')
        } finally {
            setCompleting(false)
        }
    }

    const handleGeneratePlan = async () => {
        setGenerating(true)
        try {
            const { data } = await workoutAPI.generate()
            if (data.plan) {
                const fetchedPlan = data.plan || [];
                setPlan(fetchedPlan);
                setWorkoutPlan(fetchedPlan);
                toast.success('Your personalized workout plan is ready! 🏋️')
            }
        } catch (err) {
            toast.error('Failed to generate plan. Please try again.')
        } finally {
            setGenerating(false)
        }
    }

    const handleToggleFavourite = async (ex) => {
        const existingFav = favourites.find(f => f.name === ex.name)

        setIsFavouriting(true)
        try {
            if (existingFav) {
                await favouriteAPI.remove(existingFav.id)
                setFavourites(favourites.filter(f => f.id !== existingFav.id))
                toast.success('Removed from favourites')
            } else {
                const favData = {
                    name: ex.name,
                    muscle_group: ex.muscle_group,
                    sets: String(ex.sets),
                    reps: String(ex.reps),
                    rest_seconds: parseInt(ex.rest_seconds) || 60,
                    instructions: ex.instructions,
                    video_url: ex.video?.url,
                    video_id: ex.video?.video_id
                }
                const { data } = await favouriteAPI.add(favData)
                setFavourites([...favourites, data])
                toast.success('Added to favourites! ❤️')
            }
        } catch (err) {
            toast.error('Failed to update favourites')
        } finally {
            setIsFavouriting(false)
        }
    }

    const isExerciseFavourite = (name) => favourites.some(f => f.name === name)

    if (loading) return (
        <div className="min-h-screen bg-mesh"><Navbar />
            <div className="flex items-center justify-center h-[60vh]">
                <div className="text-center"><div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" /><p className="text-muted">Loading your workout plan...</p></div>
            </div>
        </div>
    )

    if (completionMsg) return (
        <div className="min-h-screen bg-mesh"><Navbar />
            <div className="flex items-center justify-center h-[80vh]">
                <motion.div initial={{ scale: 0.8, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="glass p-12 text-center max-w-md mx-4">
                    <div className="text-6xl mb-4">🏆</div>
                    <h2 className="text-2xl font-bold text-main mb-2">Workout Complete!</h2>
                    <p className="text-purple-400 font-medium mb-6">{completionMsg.message}</p>
                    <div className="grid grid-cols-2 gap-4 mb-8">
                        <div className="glass p-4 rounded-xl"><p className="text-2xl font-bold text-orange-400">{completionMsg.calories}</p><p className="text-muted text-sm">Calories Burned</p></div>
                        <div className="glass p-4 rounded-xl"><p className="text-2xl font-bold text-purple-400">{completionMsg.sets}</p><p className="text-muted text-sm">Sets Completed</p></div>
                    </div>
                    <button onClick={() => { setCompletionMsg(null) }} className="btn-primary w-full justify-center py-3">Continue 💪</button>
                </motion.div>
            </div>
        </div>
    )

    return (
        <div className="min-h-screen bg-mesh">
            <Navbar />
            <div className="max-w-5xl mx-auto px-6 py-8">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6 flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-main mb-1">Workout Plan 🏋️</h1>
                        <p className="text-muted">Your personalized 7-day fitness program</p>
                    </div>
                </motion.div>

                {plan.length === 0 ? (
                    <div className="glass p-12 text-center rounded-3xl">
                        <div className="text-5xl mb-4">🏃</div>
                        <h2 className="text-xl font-bold text-main mb-2">No workout plan yet</h2>
                        <p className="text-muted mb-6">
                            {user?.assessment_completed === 'yes'
                                ? "Assessment complete! Click below to generate your personalized fitness program."
                                : "Complete your health assessment to generate a personalized plan"}
                        </p>
                        {user?.assessment_completed === 'yes' ? (
                            <button onClick={handleGeneratePlan} disabled={generating} className="btn-primary px-8 py-3">
                                {generating ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Generating...</> : "Generate My Plan →"}
                            </button>
                        ) : (
                            <button onClick={() => navigate('/assessment')} className="btn-primary px-8 py-3">Start Assessment →</button>
                        )}
                    </div>
                ) : (
                    <>
                        {/* Day Selector */}
                        <div className="flex gap-2 overflow-x-auto pb-2 mb-6">
                            {plan.map(p => (
                                <button key={p.day} onClick={() => setSelectedDay(p.day)}
                                    className={`flex-shrink-0 px-4 py-2 rounded-xl text-sm font-medium transition-all ${selectedDay === p.day ? 'bg-purple-500 text-white' : 'glass-card text-muted hover:text-main'}`}>
                                    {p.day_name?.slice(0, 3) || `Day ${p.day}`}
                                </button>
                            ))}
                        </div>

                        {todayPlan && (
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                {/* Exercises */}
                                <div className="lg:col-span-2 space-y-4">
                                    {/* Warmup */}
                                    {todayPlan.warmup && (
                                        <div className="glass-card p-4 border-l-4 border-yellow-500">
                                            <p className="text-yellow-400 text-sm font-semibold mb-1">🔥 Warmup</p>
                                            <p className="text-main text-sm opacity-80">{todayPlan.warmup}</p>
                                        </div>
                                    )}

                                    {/* Exercise List */}
                                    <div className="space-y-3">
                                        {(todayPlan.exercises || []).length > 0 ? (
                                            todayPlan.exercises.map((ex, i) => {
                                                const videoData = getExerciseVideo(ex)
                                                return (
                                                    <motion.div key={i} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }} className="glass-card p-4">
                                                        <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpandedEx(expandedEx === i ? null : i)}>
                                                            <div className="flex items-center gap-3">
                                                                <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center text-purple-400 text-sm font-bold">{i + 1}</div>
                                                                <div>
                                                                    <p className="text-main font-medium">{ex.name}</p>
                                                                    <p className="text-muted text-xs">{ex.muscle_group || ''} • {ex.sets} sets × {ex.reps} reps</p>
                                                                </div>
                                                            </div>
                                                            <div className="flex items-center gap-2">
                                                                <button
                                                                    onClick={(e) => { e.stopPropagation(); handleToggleFavourite(ex) }}
                                                                    className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${isExerciseFavourite(ex.name) ? 'bg-red-500/20 text-red-500' : 'bg-white/5 text-slate-500 hover:text-red-400 hover:bg-red-500/10'}`}
                                                                >
                                                                    <Heart size={14} fill={isExerciseFavourite(ex.name) ? "currentColor" : "none"} />
                                                                </button>
                                                                {videoData?.video_id && (
                                                                    <button onClick={(e) => { e.stopPropagation(); setVideoEx(videoEx === i ? null : i) }}
                                                                        className="w-8 h-8 rounded-lg bg-red-500/20 flex items-center justify-center text-red-400 hover:bg-red-500/30 transition-all"
                                                                        title="Play video in dashboard">
                                                                        <Youtube size={14} />
                                                                    </button>
                                                                )}
                                                                {expandedEx === i ? <ChevronUp size={16} className="text-muted" /> : <ChevronDown size={16} className="text-muted" />}
                                                            </div>
                                                        </div>

                                                        <AnimatePresence>
                                                            {expandedEx === i && (
                                                                <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                                                                    <div className="mt-3 pt-3 border-t border-slate-700/10 space-y-2">
                                                                        {ex.instructions && <p className="text-muted text-sm">{ex.instructions}</p>}
                                                                        <div className="flex gap-4 text-sm">
                                                                            <span className="text-muted">⏱ Rest: <span className="text-main font-medium">{ex.rest_seconds}s</span></span>
                                                                            <span className="text-muted">💪 Sets: <span className="text-main font-medium">{ex.sets}</span></span>
                                                                            <span className="text-muted">🔁 Reps: <span className="text-main font-medium">{ex.reps}</span></span>
                                                                        </div>
                                                                        {videoData && (
                                                                            <a href={videoData.url} target="_blank" rel="noreferrer" className="flex items-center gap-2 text-red-400 text-sm hover:text-red-300 font-medium">
                                                                                <Youtube size={14} /> Watch Tutorial →
                                                                            </a>
                                                                        )}
                                                                    </div>
                                                                </motion.div>
                                                            )}
                                                        </AnimatePresence>

                                                        {/* YouTube Embed */}
                                                        {videoEx === i && videoData?.video_id && (
                                                            <div className="mt-3">
                                                                <iframe
                                                                    src={`https://www.youtube.com/embed/${videoData.video_id}`}
                                                                    className="w-full rounded-xl aspect-video"
                                                                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                                                                    allowFullScreen
                                                                />
                                                            </div>
                                                        )}
                                                    </motion.div>
                                                )
                                            })
                                        ) : (
                                            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass-card p-12 text-center rounded-3xl border-dashed border-2 border-purple-500/20">
                                                <div className="text-5xl mb-4">🧘</div>
                                                <h3 className="text-2xl font-bold text-main mb-2">Rest & Recovery</h3>
                                                <p className="text-muted mb-6">Rest is just as important as the workout. Your muscles need time to repair and grow stronger.</p>
                                                <div className="inline-block px-4 py-2 rounded-full bg-purple-500/10 text-purple-400 text-sm font-medium border border-purple-500/20">
                                                    Enjoy your day off! ✨
                                                </div>
                                            </motion.div>
                                        )}
                                    </div>

                                    {/* Cooldown */}
                                    {todayPlan.cooldown && (
                                        <div className="glass-card p-4 border-l-4 border-blue-500">
                                            <p className="text-blue-400 text-sm font-semibold mb-1">❄️ Cooldown</p>
                                            <p className="text-main text-sm opacity-80">{todayPlan.cooldown}</p>
                                        </div>
                                    )}
                                </div>

                                {/* Sidebar */}
                                <div className="space-y-6">

                                    {/* Stats */}
                                    <div className="glass-card p-5">
                                        <h3 className="text-main font-semibold mb-3">Today's Stats</h3>
                                        <div className="space-y-3">
                                            <div className="flex justify-between">
                                                <span className="text-muted text-sm">Duration</span>
                                                <span className="text-main font-medium">
                                                    {(todayPlan.exercises || []).length > 0 ? `${todayPlan.duration_minutes} min` : 'Rest Day'}
                                                </span>
                                            </div>
                                            <div className="flex justify-between"><span className="text-muted text-sm">Exercises</span><span className="text-main font-medium">{todayPlan.exercises?.length || 0}</span></div>
                                            <div className="flex justify-between"><span className="text-muted text-sm">Est. Calories</span><span className="text-orange-400 font-bold">{todayPlan.calories_estimate || '~200'} kcal</span></div>
                                        </div>
                                    </div>

                                    {/* Timer */}
                                    <div className="glass-card p-4">
                                        <h3 className="text-main font-semibold mb-3 flex items-center gap-2"><Timer size={16} /> Workout Timer</h3>
                                        <WorkoutTimer onComplete={handleComplete} />
                                    </div>

                                    {/* Complete button */}
                                    <motion.button
                                        whileHover={{ scale: 1.03 }}
                                        onClick={handleComplete}
                                        disabled={completing}
                                        className="btn-primary w-full justify-center py-4 rounded-2xl disabled:opacity-60"
                                    >
                                        {completing ? <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Logging...</> : <><Trophy size={18} /> Mark Complete 🎉</>}
                                    </motion.button>

                                    {/* Tips */}
                                    {todayPlan.tips && (
                                        <div className="glass-card p-4">
                                            <p className="text-purple-400 text-sm font-semibold mb-2">💡 Tips</p>
                                            <p className="text-muted text-sm">{typeof todayPlan.tips === 'string' ? todayPlan.tips : JSON.stringify(todayPlan.tips)}</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
