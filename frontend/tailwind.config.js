/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class', '[data-theme="dark"]'],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Noto Sans SC"', '"Geist Sans"', 'system-ui', 'sans-serif'],
        display: ['"Newsreader"', '"Noto Serif SC"', 'Georgia', 'serif'],
        mono: ['"Geist Mono"', '"JetBrains Mono"', 'monospace'],
        terminal: ['"JetBrains Mono"', '"Geist Mono"', 'monospace'],
      },
      colors: {
        x: {
          black: 'hsl(var(--x-black) / <alpha-value>)',
          dark: 'hsl(var(--x-dark) / <alpha-value>)',
          darker: 'hsl(var(--x-darker) / <alpha-value>)',
          gray: 'hsl(var(--x-gray) / <alpha-value>)',
          'light-gray': 'hsl(var(--x-light-gray) / <alpha-value>)',
          border: 'hsl(var(--x-border) / <alpha-value>)',
          'border-hover': 'hsl(var(--x-border-hover) / <alpha-value>)',
          blue: 'hsl(var(--x-blue) / <alpha-value>)',
          'blue-hover': 'hsl(var(--x-blue-hover) / <alpha-value>)',
          green: 'hsl(var(--x-green) / <alpha-value>)',
          pink: 'hsl(var(--x-pink) / <alpha-value>)',
          yellow: 'hsl(var(--x-yellow) / <alpha-value>)',
          red: 'hsl(var(--x-red) / <alpha-value>)',
          // Cyber terminal accents
          cyan: 'hsl(var(--x-cyan) / <alpha-value>)',
          magenta: 'hsl(var(--x-magenta) / <alpha-value>)',
          lime: 'hsl(var(--x-lime) / <alpha-value>)',
          violet: 'hsl(var(--x-violet) / <alpha-value>)',
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
        'border-flow': 'borderFlow 3s linear infinite',
        'scan-line': 'scanLine 4s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
        'typing': 'typing 0.8s steps(8) infinite',
        'flicker': 'flicker 3s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(30px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 5px hsl(var(--x-cyan) / 0.3), 0 0 20px hsl(var(--x-cyan) / 0.1)' },
          '50%': { boxShadow: '0 0 10px hsl(var(--x-cyan) / 0.6), 0 0 40px hsl(var(--x-cyan) / 0.2)' },
        },
        borderFlow: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '200% 50%' },
        },
        scanLine: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        typing: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        flicker: {
          '0%, 100%': { opacity: '1' },
          '92%': { opacity: '1' },
          '93%': { opacity: '0.3' },
          '94%': { opacity: '1' },
          '96%': { opacity: '0.5' },
          '97%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
