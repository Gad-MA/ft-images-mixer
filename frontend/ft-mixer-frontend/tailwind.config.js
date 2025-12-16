/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Professional dark theme palette
        background: '#1a1a1a',
        surface: '#2d2d2d',
        'surface-lighter': '#3d3d3d',
        border: '#4a4a4a',
        primary: '#3b82f6', // A nice professional blue
        text: '#e5e5e5',
        'text-muted': '#a3a3a3',
      }
    },
  },
  plugins: [],
}