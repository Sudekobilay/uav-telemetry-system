/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        mil: {
          base: '#0a0c10',
          panel: '#0f131a',
          card: '#151a24',
          cardInner: '#0d1117',
          hover: '#1c2330',
          selected: '#242e3f',
          border: '#1e2633',
          borderLight: '#2c374a',
          blue: '#6c94b8',
          sand: '#b89c68',
          red: '#9e4444',
          green: '#488255'
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}