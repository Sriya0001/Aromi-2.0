import axios from 'axios'
import useStore from '../store/useStore'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
    baseURL: API_BASE,
    headers: { 'Content-Type': 'application/json' },
})

// Inject JWT token on every request
api.interceptors.request.use((config) => {
    const token = useStore.getState().token
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Handle 401 — logout
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            useStore.getState().logout()
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

// ─── Auth ───────────────────────────────────────────
export const authAPI = {
    register: (data) => api.post('/auth/register', data),

    login: (username, password) => {
        const form = new URLSearchParams()
        form.append('username', username)
        form.append('password', password)
        return api.post('/auth/login', form, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        })
    },

    getMe: () => api.get('/users/me'),
    updateProfile: (data) => api.put('/users/profile', data),
}

// ─── Workout ─────────────────────────────────────────
export const workoutAPI = {
    generate: () => api.post('/workout/generate'),
    getPlan: () => api.get('/workout/plan'),
    getToday: (day) => api.get('/workout/today', { params: { day } }),
    completeWorkout: (calories, sets, duration) =>
        api.post('/workout/complete', null, {
            params: { calories_burned: calories, sets_completed: sets, duration_minutes: duration }
        }),
}

// ─── Nutrition ───────────────────────────────────────
export const nutritionAPI = {
    generate: () => api.post('/nutrition/generate'),
    getPlan: () => api.get('/nutrition/plan'),
    getShoppingList: () => api.get('/nutrition/shopping-list'),
}

// ─── Progress ────────────────────────────────────────
export const progressAPI = {
    log: (data) => api.post('/progress/log', data),
    getHistory: () => api.get('/progress/history'),
    getStats: () => api.get('/progress/stats'),
}

// ─── AI / AROMI ──────────────────────────────────────
export const aiAPI = {
    chat: (message) => api.post('/ai/chat', { message }),
    getChatHistory: () => api.get('/ai/chat/history'),
    generateFullPlan: () => api.post('/ai/generate-plan'),
}

// ─── Reviews ─────────────────────────────────────────
export const reviewAPI = {
    getAll: () => api.get('/reviews/'),
    create: (data) => api.post('/reviews/', data),
}

export const favouriteAPI = {
    getAll: () => api.get('/favourites/'),
    add: (data) => api.post('/favourites/', data),
    remove: (id) => api.delete(`/favourites/${id}`),
}

// ─── Calendar ────────────────────────────────────────
export const calendarAPI = {
    authorize: () => api.get('/calendar/authorize'),
}

// ─── Health Data Logging ──────────────────────────────
export const logSleep = (data) => api.post('/health-data/sleep', data);
export const logHydration = (data) => api.post('/health-data/hydration', data);
export const logProgress = (data) => api.post('/health-data/progress', data);
export const submitWorkoutFeedback = (data) => api.post('/health-data/workout-feedback', data);
export const submitFeedback = (data) => api.post('/health-data/feedback', data);

// ─── Memory ──────────────────────────────────────────
export const getMemories = () => api.get('/memory/');
export const triggerMemoryExtraction = () => api.post('/memory/extract');

// ─── Evaluation ──────────────────────────────────────
export const getEvaluationReport = () => api.get('/evaluation/report');
export const getAdherenceMetrics = (days = 7) => api.get(`/evaluation/adherence?days=${days}`);

// ─── Profile ─────────────────────────────────────────
export const getHealthProfile = () => api.get('/users/profile');
export const addMedicalCondition = (data) => api.post('/users/medical-conditions', data);
export const addInjury = (data) => api.post('/users/injuries', data);
export const getMedicalConditions = () => api.get('/users/medical-conditions');

// ─── New Plan Generation ─────────────────────────────
export const generatePlanWithAgents = () => api.post('/ai/generate-plan');
export const getSessionReasoning = (sessionId) => api.get(`/ai/session-reasoning/${sessionId}`);

export default api
