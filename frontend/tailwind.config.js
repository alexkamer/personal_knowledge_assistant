/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Knowledge Garden Color Palette
      colors: {
        // Primary: Indigo (Depth, wisdom, intelligence)
        indigo: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          300: '#A5B4FC',
          400: '#818CF8',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
          800: '#3730A3',
          900: '#312E81',
        },
        // Accent: Amber (Growth, warmth, insight)
        amber: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
        // Secondary Accent: Lavender (Creativity, connection, synthesis)
        lavender: {
          50: '#FAF5FF',
          100: '#F3E8FF',
          200: '#E9D5FF',
          300: '#D8B4FE',
          400: '#C084FC',
          500: '#A855F7',
          600: '#9333EA',
          700: '#7E22CE',
          800: '#6B21A8',
          900: '#581C87',
        },
        // Neutral: Warm Stone (replacing cold grays)
        stone: {
          50: '#FAFAF9',
          100: '#F5F5F4',
          200: '#E7E5E4',
          300: '#D6D3D1',
          400: '#A8A29E',
          500: '#78716C',
          600: '#57534E',
          700: '#44403C',
          800: '#292524',
          900: '#1C1917',
          950: '#0F0E13',  // Deep indigo-tinted black for dark mode
        },
      },
      // Typography: Inter Variable
      fontFamily: {
        sans: ['Inter Variable', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Menlo', 'monospace'],
      },
      // Enhanced shadows with colored tints
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(99, 102, 241, 0.05)',
        'DEFAULT': '0 4px 6px -1px rgba(99, 102, 241, 0.08), 0 2px 4px -1px rgba(99, 102, 241, 0.04)',
        'md': '0 6px 8px -2px rgba(99, 102, 241, 0.1), 0 3px 5px -1px rgba(99, 102, 241, 0.05)',
        'lg': '0 10px 15px -3px rgba(99, 102, 241, 0.12), 0 4px 6px -2px rgba(99, 102, 241, 0.06)',
        'xl': '0 20px 25px -5px rgba(99, 102, 241, 0.15), 0 10px 10px -5px rgba(99, 102, 241, 0.08)',
        '2xl': '0 25px 50px -12px rgba(99, 102, 241, 0.25)',
        'glow': '0 0 20px rgba(99, 102, 241, 0.4)',
        'inner': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
        'none': 'none',
      },
      // Animation durations
      transitionDuration: {
        '150': '150ms',
        '200': '200ms',
        '300': '300ms',
      },
      // Letter spacing adjustments
      letterSpacing: {
        tightest: '-0.02em',
        tighter: '-0.01em',
        wider: '0.02em',
      },
      // Backdrop blur for glass-morphism
      backdropBlur: {
        xs: '2px',
        sm: '4px',
        md: '12px',
        lg: '16px',
        xl: '24px',
      },
      // Custom background colors for glass effect
      backgroundColor: {
        'glass-light': 'rgba(255, 255, 255, 0.08)',
        'glass-dark': 'rgba(26, 24, 37, 0.7)',
      },
      // Border colors for glass effect
      borderColor: {
        'glass-light': 'rgba(255, 255, 255, 0.12)',
        'glass-dark': 'rgba(255, 255, 255, 0.08)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
}
