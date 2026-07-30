import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Eye, EyeOff, UserPlus } from 'lucide-react'
import toast from 'react-hot-toast'
import { authAPI } from '../services/api'

export default function RegisterPage() {
    const navigate = useNavigate()
    const [form, setForm] = useState({ username: '', email: '', password: '', confirm: '' })
    const [show, setShow] = useState(false)
    const [loading, setLoading] = useState(false)

    const handleSubmit = async (e) => {
        e.preventDefault()
        if (form.password !== form.confirm) {
            toast.error('Passwords do not match')
            return
        }
        if (form.password.length < 6) {
            toast.error('Password must be at least 6 characters')
            return
        }
        setLoading(true)
        try {
            await authAPI.register({ username: form.username, email: form.email, password: form.password })
            toast.success('Account created! Please log in.')
            navigate('/login')
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Registration failed.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="min-h-screen bg-mesh flex items-center justify-center px-4 py-12">
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-1/3 right-1/4 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl" />
                <div className="absolute bottom-1/3 left-1/4 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl" />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                className="w-full max-w-md glass p-8 relative z-10"
            >
                <div className="text-center mb-8">
                    <div className="w-14 h-14 rounded-2xl icon-purple flex items-center justify-center text-2xl mx-auto mb-4">✦</div>
                    <h1 className="text-2xl font-bold text-white">Join ArogyaMitra</h1>
                    <p className="text-slate-400 text-sm mt-1">Start your AI-powered fitness journey today</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Username</label>
                        <input type="text" className="input-dark" placeholder="your_username"
                            value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Email</label>
                        <input type="email" className="input-dark" placeholder="you@email.com"
                            value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Password</label>
                        <div className="relative">
                            <input type={show ? 'text' : 'password'} className="input-dark pr-12" placeholder="Min 6 characters"
                                value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required />
                            <button type="button" onClick={() => setShow(!show)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300">
                                {show ? <EyeOff size={18} /> : <Eye size={18} />}
                            </button>
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">Confirm Password</label>
                        <input type="password" className="input-dark" placeholder="Re-enter password"
                            value={form.confirm} onChange={e => setForm({ ...form, confirm: e.target.value })} required />
                    </div>

                    <motion.button type="submit" disabled={loading} whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}
                        className="btn-primary w-full justify-center py-3 text-base mt-2 disabled:opacity-60">
                        {loading ? (
                            <span className="flex items-center gap-2">
                                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                Creating account...
                            </span>
                        ) : <><UserPlus size={18} /> Create Account</>}
                    </motion.button>
                </form>

                <p className="text-center text-slate-400 text-sm mt-6">
                    Already have an account?{' '}
                    <Link to="/login" className="text-purple-400 hover:text-purple-300 font-medium">Log in</Link>
                </p>
            </motion.div>
        </div>
    )
}
