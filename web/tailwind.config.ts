import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e1effe',
          200: '#c3dffe',
          300: '#a5cffe',
          400: '#87bffe',
          500: '#69affd',
          600: '#4b9ffd',
          700: '#2d8ffd',
          800: '#0f7ffd',
          900: '#0a66cc'
        },
        // Neo-tech Kid-friendly palette
        neo: {
          // Primary - Electric cyan/teal
          primary: '#00E5CC',
          'primary-light': '#5FFBF1',
          'primary-dark': '#00B8A3',
          // Secondary - Vibrant coral
          secondary: '#FF6B6B',
          'secondary-light': '#FF9F9F',
          // Accent - Electric purple
          accent: '#A855F7',
          'accent-light': '#C084FC',
          'accent-dark': '#7C3AED',
          // Background gradients
          dark: '#0F172A',
          'dark-lighter': '#1E293B',
          'dark-card': '#1E1B4B',
          // Neon highlights
          neon: {
            cyan: '#22D3EE',
            purple: '#A78BFA',
            pink: '#F472B6',
            yellow: '#FACC15',
            green: '#4ADE80',
            orange: '#FB923C',
          },
          // Glass effects
          glass: 'rgba(255, 255, 255, 0.1)',
          'glass-border': 'rgba(255, 255, 255, 0.2)',
        },
        // Keep wally for backwards compatibility
        wally: {
          primary: '#00E5CC',
          'primary-light': '#5FFBF1',
          'primary-dark': '#00B8A3',
          secondary: '#FF6B6B',
          'secondary-light': '#FF9F9F',
          bg: '#0F172A',
          'bg-light': '#1E293B',
          purple: '#A855F7',
          pink: '#F472B6',
          yellow: '#FACC15',
          green: '#4ADE80',
          owl: '#A78BFA',
          'owl-dark': '#7C3AED'
        }
      },
      backgroundImage: {
        'neo-gradient': 'linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #312E81 100%)',
        'neo-card': 'linear-gradient(135deg, rgba(30, 27, 75, 0.8) 0%, rgba(49, 46, 129, 0.6) 100%)',
        'neo-glow': 'radial-gradient(ellipse at center, rgba(0, 229, 204, 0.15) 0%, transparent 70%)',
        'neo-accent': 'linear-gradient(135deg, #00E5CC 0%, #A855F7 100%)',
        'neo-warm': 'linear-gradient(135deg, #FF6B6B 0%, #FB923C 100%)',
      },
      boxShadow: {
        'neo-sm': '0 0 10px rgba(0, 229, 204, 0.3)',
        'neo': '0 0 20px rgba(0, 229, 204, 0.4)',
        'neo-lg': '0 0 40px rgba(0, 229, 204, 0.5)',
        'neo-purple': '0 0 20px rgba(168, 85, 247, 0.4)',
        'neo-pink': '0 0 20px rgba(244, 114, 182, 0.4)',
        'neo-orange': '0 0 20px rgba(251, 146, 60, 0.4)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.3)',
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(0, 229, 204, 0.5)' },
          '100%': { boxShadow: '0 0 20px rgba(0, 229, 204, 0.8), 0 0 30px rgba(168, 85, 247, 0.4)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
    },
  },
  darkMode: 'class'
};

export default config;

