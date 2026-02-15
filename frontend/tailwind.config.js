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
        primary: {
          bg: '#212121',
          secondary: '#2f2f2f',
          accent: '#10a37f',
        },
        user: {
          bg: '#2f4f4f',
        },
        bot: {
          bg: '#1e1e1e',
        }
      },
      fontFamily: {
        sans: ['Vazirmatn', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}