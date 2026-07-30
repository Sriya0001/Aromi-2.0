import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import useStore from './store/useStore'
import LandingPage from './pages/LandingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import AssessmentPage from './pages/AssessmentPage'
import WorkoutPage from './pages/WorkoutPage'
import NutritionPage from './pages/NutritionPage'
import ProgressPage from './pages/ProgressPage'
import ProfilePage from './pages/ProfilePage'
import CalendarPage from './pages/CalendarPage'
import Onboarding from './pages/Onboarding'
import MemoryViewer from './components/MemoryViewer'
import HealthLogger from './components/HealthLogger'
import AROMIAssistant from './components/AROMIAssistant'

function PrivateRoute({ children }) {
    const token = useStore(s => s.token)
    return token ? children : <Navigate to="/login" replace />
}

function App() {
    const theme = useStore(s => s.theme)

    useEffect(() => {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark')
        } else {
            document.documentElement.classList.remove('dark')
        }
    }, [theme])

    return (
        <BrowserRouter>
            <Toaster
                position="top-right"
                toastOptions={{
                    style: {
                        background: '#12122a',
                        color: '#e2e8f0',
                        border: '1px solid rgba(124,58,237,0.3)',
                        borderRadius: '12px',
                    },
                }}
            />
            <Routes>
                <Route path="/" element={<LandingPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/dashboard" element={<PrivateRoute><DashboardPage /></PrivateRoute>} />
                <Route path="/assessment" element={<PrivateRoute><AssessmentPage /></PrivateRoute>} />
                <Route path="/workout" element={<PrivateRoute><WorkoutPage /></PrivateRoute>} />
                <Route path="/nutrition" element={<PrivateRoute><NutritionPage /></PrivateRoute>} />
                <Route path="/progress" element={<PrivateRoute><ProgressPage /></PrivateRoute>} />
                <Route path="/profile" element={<PrivateRoute><ProfilePage /></PrivateRoute>} />
                <Route path="/calendar" element={<PrivateRoute><CalendarPage /></PrivateRoute>} />
                <Route path="/onboarding" element={<PrivateRoute><Onboarding /></PrivateRoute>} />
                <Route path="/memory" element={<PrivateRoute><MemoryViewer /></PrivateRoute>} />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
            <AROMIAssistant />
        </BrowserRouter>
    )
}

export default App
