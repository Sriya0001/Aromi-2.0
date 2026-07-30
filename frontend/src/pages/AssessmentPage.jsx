import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, ArrowLeft, CheckCircle2 } from 'lucide-react'
import toast from 'react-hot-toast'
import Navbar from '../components/Navbar'
import { authAPI, aiAPI } from '../services/api'
import useStore from '../store/useStore'

const steps = [
    { id: 'age', label: 'How old are you?', type: 'number', placeholder: '25', key: 'age' },
    { id: 'gender', label: "What's your gender?", type: 'select', options: ['Male', 'Female', 'Other'], key: 'gender' },
    { id: 'height', label: 'What is your height? (cm)', type: 'number', placeholder: '170', key: 'height' },
    { id: 'weight', label: 'What is your weight? (kg)', type: 'number', placeholder: '70', key: 'weight' },
    { id: 'fitness_level', label: 'What is your current fitness level?', type: 'select', options: ['Beginner', 'Intermediate', 'Advanced'], key: 'fitness_level' },
    { id: 'fitness_goal', label: 'What is your primary fitness goal?', type: 'select', options: ['Weight Loss', 'Muscle Gain', 'General Fitness', 'Endurance', 'Flexibility', 'Stay Active'], key: 'fitness_goal' },
    { id: 'workout_preference', label: 'Where do you prefer to workout?', type: 'select', options: ['Home', 'Gym', 'Outdoor', 'Mixed'], key: 'workout_preference' },
    { id: 'workout_time', label: 'When do you prefer to workout?', type: 'select', options: ['Morning', 'Afternoon', 'Evening', 'Flexible'], key: 'workout_time' },
    { id: 'medical_history', label: 'Any significant medical history?', type: 'text', placeholder: 'e.g. diabetes, hypertension, or none', key: 'medical_history' },
    { id: 'health_conditions', label: 'Do you have any current health conditions?', type: 'text', placeholder: 'e.g. asthma, or none', key: 'health_conditions' },
    { id: 'injuries', label: 'Any current injuries we should know about?', type: 'text', placeholder: 'e.g. knee pain, bad back, or none', key: 'injuries' },
    { id: 'diet_preference', label: "What's your diet preference?", type: 'select', options: ['Vegetarian', 'Non-Vegetarian', 'Vegan', 'Eggetarian'], key: 'diet_preference' },
    { id: 'allergies', label: 'Do you have any food allergies?', type: 'text', placeholder: 'e.g. nuts, dairy, or none', key: 'allergies' },
    { id: 'calendar_sync', label: 'Sync workouts to Google Calendar?', type: 'select', options: ['Yes', 'No'], key: 'calendar_sync' },
]

export default function AssessmentPage() {
    const navigate = useNavigate()
    const { setUser, setWorkoutPlan, setNutritionPlan } = useStore()
    const [step, setStep] = useState(0)
    const [answers, setAnswers] = useState({})
    const [loading, setLoading] = useState(false)
    const [done, setDone] = useState(false)

    const current = steps[step]
    const progress = ((step) / steps.length) * 100

    const canNext = () => {
        const val = answers[current.key]
        return val !== undefined && val !== ''
    }

    const handleNext = async () => {
        if (!canNext()) {
            toast.error('Please answer this question first')
            return
        }
        if (step < steps.length - 1) {
            setStep(s => s + 1)
        } else {
            // Submit
            setLoading(true)
            try {
                const profileData = {
                    ...answers,
                    age: parseInt(answers.age) || null,
                    height: parseInt(answers.height) || null,
                    weight: parseInt(answers.weight) || null,
                    fitness_level: answers.fitness_level?.toLowerCase(),
                    fitness_goal: answers.fitness_goal?.toLowerCase(),
                    workout_preference: answers.workout_preference?.toLowerCase(),
                    workout_time: answers.workout_time?.toLowerCase(),
                    diet_preference: answers.diet_preference?.toLowerCase(),
                    calendar_sync: answers.calendar_sync?.toLowerCase() || 'no',
                    assessment_completed: 'yes',
                }

                await authAPI.updateProfile(profileData)
                const { data: updatedUser } = await authAPI.getMe()
                setUser(updatedUser)

                // Generate plans
                toast.success('Generating your personalized plans... ⚡', { duration: 3000 })
                try {
                    const { data } = await aiAPI.generateFullPlan()
                    if (data.workout_plan) setWorkoutPlan(data.workout_plan)
                    if (data.nutrition_plan) setNutritionPlan(data.nutrition_plan)
                    setDone(true)
                } catch (genErr) {
                    toast.error('Failed to generate plans, but your profile is saved! You can try regenerating from the Workout page.')
                    navigate('/workout')
                }
            } catch (err) {
                toast.error(err.response?.data?.detail || 'Failed to save assessment.')
            } finally {
                setLoading(false)
            }
        }
    }

    if (done) {
        return (
            <div className="min-h-screen bg-mesh flex items-center justify-center">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="glass p-12 text-center max-w-md mx-4"
                >
                    <div className="text-6xl mb-6">🎉</div>
                    <h2 className="text-2xl font-bold text-white mb-3">Your Plans Are Ready!</h2>
                    <p className="text-slate-400 mb-8">AROMI has crafted personalized workout and nutrition plans just for you!</p>
                    <div className="flex flex-col gap-3">
                        <button onClick={() => navigate('/workout')} className="btn-primary justify-center py-3">
                            View My Workout Plan 🏋️
                        </button>
                        <button onClick={() => navigate('/nutrition')} className="btn-secondary py-3 rounded-xl">
                            View Nutrition Plan 🥗
                        </button>
                        <button onClick={() => navigate('/dashboard')} className="text-slate-500 text-sm hover:text-slate-300 transition-colors">
                            Go to Dashboard
                        </button>
                    </div>
                </motion.div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-mesh">
            <Navbar />
            <div className="max-w-2xl mx-auto px-6 py-12">
                {/* Progress */}
                <div className="mb-8">
                    <div className="flex justify-between text-sm text-slate-500 mb-3">
                        <span>Question {step + 1} of {steps.length}</span>
                        <span>{Math.round(progress)}% complete</span>
                    </div>
                    <div className="w-full h-2 bg-slate-800 rounded-full">
                        <motion.div
                            className="progress-bar"
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                            transition={{ duration: 0.5 }}
                        />
                    </div>
                </div>

                {/* Question Card */}
                <AnimatePresence mode="wait">
                    <motion.div
                        key={step}
                        initial={{ opacity: 0, x: 30 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -30 }}
                        transition={{ duration: 0.3 }}
                        className="glass p-8 rounded-3xl"
                    >
                        <div className="text-purple-400 text-sm font-medium mb-2">Step {step + 1}</div>
                        <h2 className="text-2xl font-bold text-white mb-8">{current.label}</h2>

                        {current.type === 'select' ? (
                            <div className="grid grid-cols-2 gap-3">
                                {current.options.map(opt => (
                                    <motion.button
                                        key={opt}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => setAnswers({ ...answers, [current.key]: opt })}
                                        className={`p-4 rounded-xl border-2 text-left font-medium transition-all ${answers[current.key] === opt
                                            ? 'border-purple-500 bg-purple-500/20 text-white'
                                            : 'border-slate-700 bg-slate-800/50 text-slate-400 hover:border-purple-500/50'
                                            }`}
                                    >
                                        {answers[current.key] === opt && <CheckCircle2 size={14} className="inline mr-2 text-purple-400" />}
                                        {opt}
                                    </motion.button>
                                ))}
                            </div>
                        ) : (
                            <input
                                type={current.type}
                                className="input-dark text-lg py-4"
                                placeholder={current.placeholder}
                                value={answers[current.key] || ''}
                                onChange={e => setAnswers({ ...answers, [current.key]: e.target.value })}
                                onKeyDown={e => e.key === 'Enter' && handleNext()}
                                autoFocus
                            />
                        )}

                        {/* Navigation */}
                        <div className="flex justify-between mt-8">
                            <button
                                onClick={() => setStep(s => Math.max(0, s - 1))}
                                disabled={step === 0}
                                className="flex items-center gap-2 text-slate-500 hover:text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                            >
                                <ArrowLeft size={18} /> Back
                            </button>

                            <motion.button
                                onClick={handleNext}
                                disabled={loading}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className="btn-primary px-8 py-3 disabled:opacity-60"
                            >
                                {loading ? (
                                    <><div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" /> Generating...</>
                                ) : step === steps.length - 1 ? (
                                    <><CheckCircle2 size={18} /> Complete & Generate</>
                                ) : (
                                    <>Next <ArrowRight size={18} /></>
                                )}
                            </motion.button>
                        </div>
                    </motion.div>
                </AnimatePresence>
            </div>
        </div>
    )
}
