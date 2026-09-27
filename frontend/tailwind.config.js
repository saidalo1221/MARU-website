/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Temporary placeholder tokens until a MARU brand book is supplied
        // (PRD TZ2 section 45.2) — replace centrally here, not per-component.
        brand: {
          DEFAULT: '#1f6f4a',
          dark: '#154d33',
          light: '#e8f4ee',
        },
      },
    },
  },
  plugins: [],
}
