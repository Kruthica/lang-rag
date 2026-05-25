/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        surface: {
          DEFAULT: '#0f1117',
          elevated: '#161b26',
          border: '#2a3142',
        },
        accent: {
          DEFAULT: '#6366f1',
          glow: '#818cf8',
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(ellipse at top, rgba(99,102,241,0.15), transparent 50%)',
      },
    },
  },
  plugins: [],
};
