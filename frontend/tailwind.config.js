/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
        'confetti-fall': 'confettiFall 2s ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        confettiFall: {
          '0%': { opacity: '1', transform: 'translate(0, 0) rotate(0deg)' },
          '100%': { opacity: '0', transform: 'translate(var(--dx, 20px), var(--dy, 300px)) rotate(var(--rot, 720deg))' },
        },
      },
    },
  },
  plugins: [],
}
