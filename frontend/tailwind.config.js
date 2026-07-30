/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                brand: {
                    purple: '#7c3aed',
                    pink: '#ec4899',
                    cyan: '#06b6d4',
                    dark: '#0f0f1a',
                    card: '#1a1a2e',
                    border: '#2a2a4a',
                }
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
            animation: {
                'float': 'float 6s ease-in-out infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
                'gradient': 'gradient 4s ease infinite',
            },
            keyframes: {
                float: {
                    '0%, 100%': { transform: 'translateY(0px)' },
                    '50%': { transform: 'translateY(-10px)' },
                },
                glow: {
                    'from': { boxShadow: '0 0 20px #7c3aed40' },
                    'to': { boxShadow: '0 0 40px #7c3aed80, 0 0 80px #7c3aed40' },
                },
                gradient: {
                    '0%, 100%': { backgroundPosition: '0% 50%' },
                    '50%': { backgroundPosition: '100% 50%' },
                }
            }
        },
    },
    plugins: [],
}
