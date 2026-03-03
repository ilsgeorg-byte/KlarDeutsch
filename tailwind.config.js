/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",    // <-- Главное: сканировать папку app
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',  // Включаем тёмную тему через класс .dark
  theme: {
    extend: {},
  },
  plugins: [],
}
