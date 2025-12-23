/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Refined Professional Color Palette (inspired by Linear + Vercel)
      colors: {
        // Base Grays - Clean, professional dark theme
        gray: {
          950: '#0A0A0A',  // App background
          900: '#111111',  // Panel backgrounds
          850: '#171717',  // Elevated elements
          800: '#1F1F1F',  // Cards/containers
          750: '#262626',  // Hover states
          700: '#333333',  // Borders
          600: '#4D4D4D',  // Inactive elements
          500: '#737373',  // Secondary text
          400: '#A3A3A3',  // Tertiary text
          300: '#D4D4D4',  // Disabled states
        },
        // Single Primary Accent (purple like Linear)
        primary: {
          400: '#A78BFA',  // Light variant
          500: '#8B5CF6',  // Primary actions, active states
          600: '#7C3AED',  // Hover
          700: '#6D28D9',  // Pressed/active
        },
        // Success Green (subtle, professional)
        success: {
          400: '#34D399',
          500: '#10B981',  // Success states
          600: '#059669',  // Hover
        },
        // Warning/Attention Yellow
        warning: {
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706',
        },
        // Danger Red (subtle)
        danger: {
          400: '#F87171',
          500: '#EF4444',  // Danger/delete
          600: '#DC2626',  // Hover
        },
        // Text Colors (semantic naming)
        text: {
          primary: '#FFFFFF',     // Primary text
          secondary: '#A3A3A3',   // Secondary text
          tertiary: '#737373',    // Tertiary text
          disabled: '#525252',    // Disabled text
        },
      },
      // Typography: System fonts for performance
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          'sans-serif',
        ],
        mono: [
          '"SF Mono"',
          'Monaco',
          '"Cascadia Code"',
          '"Roboto Mono"',
          'Consolas',
          'monospace',
        ],
      },
      // Subtle, professional shadows (no glow)
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.15)',
        'DEFAULT': '0 1px 3px 0 rgba(0, 0, 0, 0.2), 0 1px 2px 0 rgba(0, 0, 0, 0.12)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.2), 0 2px 4px -1px rgba(0, 0, 0, 0.12)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.08)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.08)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        'inner': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
        'none': 'none',
      },
      // Smooth animations
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
      },
      // Letter spacing
      letterSpacing: {
        tightest: '-0.02em',
        tighter: '-0.01em',
        wider: '0.02em',
      },
      // Backdrop blur for glass effects
      backdropBlur: {
        xs: '2px',
        sm: '4px',
        md: '12px',
        lg: '16px',
        xl: '24px',
      },
      // Simple animations (no sci-fi effects)
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-down': {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'scale-in': {
          '0%': { transform: 'scale(0.95)', opacity: '0' },
          '100%': { transform: 'scale(1)', opacity: '1' },
        },
        'pulse-subtle': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.2s ease-out',
        'slide-up': 'slide-up 0.3s ease-out',
        'slide-down': 'slide-down 0.3s ease-out',
        'scale-in': 'scale-in 0.2s ease-out',
        'pulse-subtle': 'pulse-subtle 2s ease-in-out infinite',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
