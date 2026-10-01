/** @type {import('tailwindcss').Config} */
// Every design value comes from src/styles/tokens.css (PRD ТЗ№2 §45, §60): change the
// variables there, not the components.
const token = (name) => `rgb(var(--color-${name}) / <alpha-value>)`

export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    // PRD §51: mobile 320-767, tablet 768+, desktop 1024+, large desktop 1440+.
    screens: {
      sm: '640px',
      md: '768px',
      lg: '1024px',
      xl: '1280px',
      '2xl': '1440px',
    },
    extend: {
      colors: {
        brand: {
          DEFAULT: token('brand'),
          dark: token('brand-dark'),
          light: token('brand-light'),
        },
        danger: token('danger'),
        success: token('success'),
        warning: token('warning'),
      },
      fontFamily: {
        sans: ['var(--font-sans)'],
      },
      fontSize: {
        h1: ['var(--text-h1)', { lineHeight: '1.2', fontWeight: '700' }],
        h2: ['var(--text-h2)', { lineHeight: '1.25', fontWeight: '700' }],
        h3: ['var(--text-h3)', { lineHeight: '1.3', fontWeight: '600' }],
        body: ['var(--text-body)', { lineHeight: '1.5' }],
        caption: ['var(--text-caption)', { lineHeight: '1.4' }],
        button: ['var(--text-button)', { lineHeight: '1.25', fontWeight: '500' }],
        label: ['var(--text-label)', { lineHeight: '1.2', fontWeight: '500' }],
      },
      borderRadius: {
        token: 'var(--radius-md)',
      },
      boxShadow: {
        token: 'var(--shadow-md)',
      },
      transitionDuration: {
        fast: 'var(--duration-fast)',
        base: 'var(--duration-base)',
      },
      maxWidth: {
        container: 'var(--container-max)',
      },
    },
  },
  plugins: [],
}
