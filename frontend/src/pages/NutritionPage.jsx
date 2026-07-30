import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ShoppingCart, ExternalLink, ChevronDown, ChevronUp, Utensils } from 'lucide-react'
import Navbar from '../components/Navbar'
import ShoppingList from '../components/ShoppingList'
import { nutritionAPI } from '../services/api'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import useStore from '../store/useStore'

const MEAL_COLORS = { breakfast: 'icon-orange', lunch: 'icon-green', dinner: 'icon-blue', mid_morning_snack: 'icon-cyan', evening_snack: 'icon-purple' }
const MEAL_EMOJIS = { breakfast: '🌅', lunch: '☀️', dinner: '🌙', mid_morning_snack: '🍎', evening_snack: '🍵' }

function MacroBar({ label, value, total, color }) {
    const pct = total ? Math.round((value / total) * 100) : 0
    return (
        <div>
            <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-400">{label}</span>
                <span className="text-white font-medium">{Math.round(value)}g ({pct}%)</span>
            </div>
            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <motion.div initial={{ width: 0 }} animate={{ width: `${pct}%` }} transition={{ duration: 0.8, delay: 0.2 }}
                    className="h-full rounded-full" style={{ background: color }} />
            </div>
        </div>
    )
}

export default function NutritionPage() {
    const navigate = useNavigate()
    const { user, nutritionPlan, setNutritionPlan } = useStore()
    const [plan, setPlan] = useState([])
    const [shopping, setShopping] = useState({ items: [], bigbasket_url: '' })
    const [selectedDay, setSelectedDay] = useState(new Date().getDay() || 7)
    const [expandedMeal, setExpandedMeal] = useState(null)
    const [activeTab, setActiveTab] = useState('today') // 'today', 'week', 'shopping'
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (nutritionPlan && nutritionPlan.length > 0) {
            setPlan(nutritionPlan)
        }
    }, [nutritionPlan])

    useEffect(() => {
        Promise.all([nutritionAPI.getPlan(), nutritionAPI.getShoppingList()])
            .then(([plan, shop]) => {
                setPlan(plan.data.plan || [])
                setShopping(shop.data)
                setLoading(false)
            })
            .catch(() => setLoading(false))
    }, [])

    const todayPlan = plan.find(p => p.day === selectedDay)
    const meals = todayPlan?.meals || {}
    const totalMacros = (todayPlan?.protein || 0) + (todayPlan?.carbs || 0) + (todayPlan?.fat || 0)

    if (loading) return (
        <div className="min-h-screen bg-mesh"><Navbar />
            <div className="flex items-center justify-center h-[60vh]">
                <div className="text-center"><div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" /><p className="text-slate-400">Loading your nutrition plan...</p></div>
            </div>
        </div>
    )

    return (
        <div className="min-h-screen bg-mesh">
            <Navbar />
            <div className="max-w-5xl mx-auto px-6 py-8">
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="mb-6">
                    <h1 className="text-3xl font-bold text-white mb-1">Nutrition Plan 🥗</h1>
                    <p className="text-slate-400">Your AI-crafted 7-day Indian meal plan</p>
                </motion.div>

                {plan.length === 0 ? (
                    <div className="glass p-12 text-center rounded-3xl">
                        <div className="text-5xl mb-4">🥗</div>
                        <h2 className="text-xl font-bold text-white mb-2">No nutrition plan yet</h2>
                        <p className="text-slate-400 mb-6">
                            {user?.assessment_completed === 'yes'
                                ? "Assessment complete! Click below to generate your personalized nutrition program."
                                : "Complete your health assessment to get a personalized meal plan"}
                        </p>
                        {user?.assessment_completed === 'yes' ? (
                            <button
                                onClick={async () => {
                                    try {
                                        setLoading(true)
                                        const genRes = await nutritionAPI.generate()
                                        if (genRes.data.plan) {
                                            setPlan(genRes.data.plan)
                                            setNutritionPlan(genRes.data.plan)
                                        }
                                        toast.success('Your personalized nutrition plan is ready! 🥗')
                                    } catch (err) {
                                        toast.error('Failed to generate plan. Please try again.')
                                    } finally {
                                        setLoading(false)
                                    }
                                }}
                                className="btn-primary px-8 py-3"
                            >
                                Generate My Plan →
                            </button>
                        ) : (
                            <button onClick={() => navigate('/assessment')} className="btn-primary px-8 py-3">Start Assessment →</button>
                        )}
                    </div>
                ) : (
                    <>
                        {/* Custom Tabs */}
                        <div className="glass-card p-1.5 flex gap-1 mb-8 max-w-fit">
                            <button
                                onClick={() => setActiveTab('today')}
                                className={`px-6 py-2 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${activeTab === 'today' ? 'bg-slate-700 text-white shadow-xl' : 'text-slate-400 hover:text-white'}`}
                            >
                                <Utensils size={16} /> Today 🍱
                            </button>
                            <button
                                onClick={() => setActiveTab('shopping')}
                                className={`px-6 py-2 rounded-xl text-sm font-bold flex items-center gap-2 transition-all ${activeTab === 'shopping' ? 'bg-white text-slate-900 shadow-xl' : 'text-slate-400 hover:text-white'}`}
                            >
                                <ShoppingCart size={16} /> Shopping List 🛒
                            </button>
                        </div>

                        {activeTab === 'shopping' ? (
                            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
                                <ShoppingList items={shopping.items} bigbasketUrl={shopping.bigbasket_url} />
                            </motion.div>
                        ) : (
                            <>
                                {/* Day Selector (only for Week view or if you want it in Today too) */}
                                <div className="flex gap-2 overflow-x-auto pb-2 mb-6">
                                    {plan.map(p => (
                                        <button key={p.day} onClick={() => setSelectedDay(p.day)}
                                            className={`flex-shrink-0 px-4 py-2 rounded-xl text-sm font-medium transition-all ${selectedDay === p.day ? 'bg-purple-500 text-white' : 'glass-card text-slate-400 hover:text-white'}`}>
                                            {p.day_name?.slice(0, 3) || `Day ${p.day}`}
                                        </button>
                                    ))}
                                </div>

                                {todayPlan && (
                                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                        {/* Meals */}
                                        <div className="lg:col-span-2 space-y-3">
                                            {Object.entries(meals).map(([mealType, meal], i) => (
                                                <motion.div key={mealType} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }} className="glass-card p-4">
                                                    <div className="flex items-center justify-between cursor-pointer" onClick={() => setExpandedMeal(expandedMeal === mealType ? null : mealType)}>
                                                        <div className="flex items-center gap-3">
                                                            <span className="text-2xl">{MEAL_EMOJIS[mealType] || '🍽️'}</span>
                                                            <div>
                                                                <p className="text-slate-400 text-xs capitalize">{mealType.replace(/_/g, ' ')}</p>
                                                                <p className="text-white font-medium">{meal.name || meal}</p>
                                                            </div>
                                                        </div>
                                                        <div className="flex items-center gap-3">
                                                            {meal.calories && <span className="text-orange-400 text-sm font-medium">{meal.calories} kcal</span>}
                                                            {expandedMeal === mealType ? <ChevronUp size={16} className="text-slate-500" /> : <ChevronDown size={16} className="text-slate-500" />}
                                                        </div>
                                                    </div>
                                                    {expandedMeal === mealType && typeof meal === 'object' && (
                                                        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="mt-3 pt-3 border-t border-slate-700 space-y-4">
                                                            {meal.spoonacular && (
                                                                <div className="flex flex-col sm:flex-row gap-4 bg-slate-800/50 p-3 rounded-xl border border-slate-700/50">
                                                                    {meal.spoonacular.recipe_image && (
                                                                        <img src={meal.spoonacular.recipe_image} alt="Recipe" className="w-full sm:w-24 sm:h-24 object-cover rounded-lg shadow-md" />
                                                                    )}
                                                                    <div className="flex-1">
                                                                        <p className="text-white font-medium mb-1">
                                                                            {meal.spoonacular.recipe_title || 'Verified Recipe'} 
                                                                            {meal.spoonacular.recipe_url && (
                                                                                <a href={meal.spoonacular.recipe_url} target="_blank" rel="noreferrer" className="text-purple-400 ml-2 text-xs inline-flex items-center gap-1 hover:text-purple-300 transition-colors">
                                                                                    <ExternalLink size={12} /> View Full Recipe
                                                                                </a>
                                                                            )}
                                                                        </p>
                                                                        <div className="flex flex-wrap gap-3 text-xs text-slate-400 mb-2">
                                                                            {meal.spoonacular.ready_in_minutes && <span className="bg-slate-800 px-2 py-1 rounded-md">⏱ {meal.spoonacular.ready_in_minutes} mins</span>}
                                                                            {meal.spoonacular.spoonacular_calories && <span className="bg-orange-500/10 text-orange-400 px-2 py-1 rounded-md">🔥 {meal.spoonacular.spoonacular_calories} kcal</span>}
                                                                            {meal.spoonacular.spoonacular_protein && <span className="bg-purple-500/10 text-purple-400 px-2 py-1 rounded-md">💪 {meal.spoonacular.spoonacular_protein}g protein</span>}
                                                                        </div>
                                                                        <p className="text-xs text-green-400 flex items-center gap-1">✨ Powered by Spoonacular</p>
                                                                    </div>
                                                                </div>
                                                            )}
                                                            
                                                            <div className="space-y-2 pl-1">
                                                                {meal.ingredients && <p className="text-slate-300 text-sm">🛒 <b>Ingredients:</b> {meal.ingredients.join(', ')}</p>}
                                                                {meal.prep_time && !meal.spoonacular?.ready_in_minutes && <p className="text-slate-500 text-xs">⏱ Prep time: {meal.prep_time}</p>}
                                                                {meal.recipe_hint && <p className="text-slate-400 text-sm italic">{meal.recipe_hint}</p>}
                                                            </div>
                                                        </motion.div>
                                                    )}
                                                </motion.div>
                                            ))}
                                        </div>

                                        {/* Sidebar */}
                                        <div className="space-y-4">
                                            {/* Calories */}
                                            <div className="glass-card p-5">
                                                <h3 className="text-white font-semibold mb-1">Daily Calories</h3>
                                                <p className="text-3xl font-bold gradient-text mb-4">{todayPlan.calories} kcal</p>
                                                <div className="space-y-3">
                                                    <MacroBar label="Protein" value={todayPlan.protein || 0} total={totalMacros} color="#7c3aed" />
                                                    <MacroBar label="Carbs" value={todayPlan.carbs || 0} total={totalMacros} color="#06b6d4" />
                                                    <MacroBar label="Fat" value={todayPlan.fat || 0} total={totalMacros} color="#ec4899" />
                                                </div>
                                            </div>

                                            {/* Hydration */}
                                            <div className="glass-card p-4">
                                                <p className="text-blue-400 font-medium mb-1">💧 Hydration</p>
                                                <p className="text-slate-300 text-sm">{todayPlan.hydration || 'Drink 8-10 glasses of water'}</p>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}
