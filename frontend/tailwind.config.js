/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./assets/js/**/*.js",
    "./**/*.html"
  ],
  theme: {
    extend: {
      colors: {
        // Colores personalizados para el dashboard
        'brand': {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        'success': {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          700: '#15803d',
        },
        'warning': {
          50: '#fffbeb',
          100: '#fef3c7',
          500: '#f59e0b',
          700: '#d97706',
        },
        'danger': {
          50: '#fef2f2',
          100: '#fee2e2',
          500: '#ef4444',
          700: '#dc2626',
        }
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      fontSize: {
        'xs': '0.75rem',
        'sm': '0.875rem',
        'base': '1rem',
        'lg': '1.125rem',
        'xl': '1.25rem',
        '2xl': '1.5rem',
        '3xl': '1.875rem',
        '4xl': '2.25rem',
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      animation: {
        'spin-slow': 'spin 3s linear infinite',
        'pulse-fast': 'pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-gentle': 'bounce 2s infinite',
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
      }
    },
  },
  plugins: [
    // Plugin para forms si se necesita
    // require('@tailwindcss/forms'),
  ],
} 