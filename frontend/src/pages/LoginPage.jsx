import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Eye, EyeOff, LogIn } from 'lucide-react'
import toast from 'react-hot-toast'
import { authAPI } from '../services/api'
import useStore from '../store/useStore'

export default function LoginPage() {
    const navigate = useNavigate()
    const setAuth = useStore(s => s.setAuth)
    const [form, setForm] = useState({ username: '', password: '' })
    const [show, setShow] = useState(false)
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        setLoading(true)
        try {
            const { data } = await authAPI.login(form.username, form.password)
            const { data: user } = await (async () => {
                // Get user info with new token temporarily
                const { default: axios } = await import('axios')
                return axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/users/me`, {
                    headers: { Authorization: `Bearer ${data.access_token}` }
                })
            })()
            setAuth(user, data.access_token)
            toast.success(`Welcome back, ${user.username}! 💪`)
            navigate('/dashboard')
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Login failed. Check your credentials.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-mesh flex items-center justify-center px-4">
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/3 left-1/4 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-1/3 right-1/4 w-80 h-80 bg-pink-500/10 rounded-full blur-3xl" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="w-full max-w-md glass p-8 relative z-10"
            >
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="w-14 h-14 rounded-2xl icon-purple flex items-center justify-center text-2xl mx-auto mb-4">✦</div>
                    <h1 className="text-2xl font-bold text-white">Welcome Back</h1>
                    <p className="text-slate-400 text-sm mt-1">Login to continue your fitness journey</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Username</label>
                        <input
                            type="text"
                            className="input-dark"
                            placeholder="your_username"
                            value={form.username}
                            onChange={e => setForm({ ...form, username: e.target.value })}
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Password</label>
                        <div className="relative">
                            <input
                                type={show ? 'text' : 'password'}
                                className="input-dark pr-12"
                                placeholder="••••••••"
                                value={form.password}
                                onChange={e => setForm({ ...form, password: e.target.value })}
                                required
                            />
                            <button
                                type="button"
                                onClick={() => setShow(!show)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                            >
                                {show ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>

                    <motion.button
                        type="submit"
                        disabled={loading}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        className="btn-primary w-full justify-center py-3 text-base mt-2 disabled:opacity-60"
                    >
                        {loading ? (
                            <span className="flex items-center gap-2">
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Logging in...
                            </span>
                        ) : (
                            <><LogIn size={18} /> Login</>
                        )}
                    </motion.button>
                </form>

                <p className="text-center text-slate-400 text-sm mt-6">
                    Don't have an account?{' '}
                    <Link to="/register" className="text-purple-400 hover:text-purple-300 font-medium">
                        Sign up free
                    </Link>
                </p>
            </motion.div>
        </div>
    )
}
