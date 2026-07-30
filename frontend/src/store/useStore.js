import { create } from 'zustand'
import { persist } from 'zustand/middleware'

const useStore = create(
    persist(
        (set, get) => ({
            // Auth
            user: null,
            token: null,

            // Plans
            workoutPlan: [],
            nutritionPlan: [],

            // Progress
            progressData: [],
            stats: {
                total_calories_burned: 0,
                total_workouts: 0,
                total_healthy_meals: 0,
                streak_days: 0,
                charity_amount_inr: 0,
                people_impacted: 0,
            },

            // UI
            theme: 'dark',
            chatOpen: false,
            chatHistory: [],
            loading: false,

            // Actions
            setUser: (user) => set({ user }),
            setToken: (token) => set({ token }),
            setAuth: (user, token) => set({ user, token }),

            setWorkoutPlan: (plan) => set({ workoutPlan: plan }),
            setNutritionPlan: (plan) => set({ nutritionPlan: plan }),
            setProgressData: (data) => set({ progressData: data }),
            setStats: (stats) => set({ stats }),

            toggleChatOpen: () => set((s) => ({ chatOpen: !s.chatOpen })),
            setChatHistory: (history) => set({ chatHistory: history }),
            addChatMessage: (msg) => set((s) => ({ chatHistory: [...s.chatHistory, msg] })),

            toggleTheme: () => set((s) => {
                const newTheme = s.theme === 'dark' ? 'light' : 'dark'
                if (newTheme === 'dark') {
                    document.documentElement.classList.add('dark')
                } else {
                    document.documentElement.classList.remove('dark')
                }
                return { theme: newTheme }
            }),

            logout: () => set({
                user: null,
                token: null,
                workoutPlan: [],
                nutritionPlan: [],
                progressData: [],
                chatHistory: [],
                stats: {
                    total_calories_burned: 0,
                    total_workouts: 0,
                    total_healthy_meals: 0,
                    streak_days: 0,
                    charity_amount_inr: 0,
                    people_impacted: 0,
                }
            }),

            isAuthenticated: () => !!get().token,
        }),
        {
            name: 'arogyamitra-storage',
            partialKeys: ['user', 'token', 'workoutPlan', 'nutritionPlan', 'theme', 'chatHistory'],
        }
    )
)

export default useStore
