/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:          '#0a0c14',
        surface:     '#111827',
        'surface-2': '#1e2235',
        border:      '#1f2937',
        accent:      '#6366f1',
        'accent-2':  '#818cf8',
      },
      keyframes: {
        'orb-pulse': {
          '0%, 100%': { boxShadow: '0 0 40px #4f46e580, 0 0 80px #4f46e530' },
          '50%':      { boxShadow: '0 0 60px #6366f1b0, 0 0 120px #6366f160' },
        },
      },
      animation: {
        'orb-pulse': 'orb-pulse 3s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
