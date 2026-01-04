/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    // Django templates
    "../../../Templates/**/*.html",
    "../../../class/templates/**/*.html",
    "../../../**/templates/**/*.html",
    
    // Python files with Tailwind classes
    "../../../class/**/*.py",
    "../../../**/views.py",
    "../../../**/forms.py",
    
    // JavaScript files
    "../../../static/**/*.js",
    "../../../**/static/**/*.js",
  ],
  
  // Enable JIT mode for faster compilation
  mode: 'jit',
  
  theme: {
    extend: {
      // Custom colors for admin interface
      colors: {
        'admin-primary': '#1f2937',
        'admin-secondary': '#374151',
        'admin-accent': '#3b82f6',
        'admin-success': '#10b981',
        'admin-warning': '#f59e0b',
        'admin-error': '#ef4444',
        'admin-info': '#06b6d4',
      },
      
      // Custom spacing for consistent UI
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      
      // Custom animations for better UX
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'pulse-slow': 'pulse 3s infinite',
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      
      // Custom font sizes
      fontSize: {
        'xs': '0.75rem',
        'sm': '0.875rem',
        'base': '1rem',
        'lg': '1.125rem',
        'xl': '1.25rem',
        '2xl': '1.5rem',
        '3xl': '1.875rem',
      },
    },
  },
  
  plugins: [
    // Add forms plugin for better form styling
    require('@tailwindcss/forms')({
      strategy: 'class',
    }),
    
    // Add typography plugin for content
    require('@tailwindcss/typography'),
    
    // Custom plugin for admin-specific utilities
    function({ addUtilities, addComponents, theme }) {
      // Admin-specific utilities
      addUtilities({
        '.admin-card': {
          '@apply bg-white rounded-lg shadow-sm border border-gray-200 p-6': {},
        },
        '.admin-button': {
          '@apply px-4 py-2 rounded-lg font-medium transition-colors duration-200': {},
        },
        '.admin-button-primary': {
          '@apply admin-button bg-blue-600 text-white hover:bg-blue-700': {},
        },
        '.admin-button-secondary': {
          '@apply admin-button bg-gray-200 text-gray-800 hover:bg-gray-300': {},
        },
        '.admin-input': {
          '@apply w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500': {},
        },
        '.admin-table': {
          '@apply min-w-full divide-y divide-gray-200': {},
        },
        '.admin-table-header': {
          '@apply px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider': {},
        },
        '.admin-table-cell': {
          '@apply px-6 py-4 whitespace-nowrap text-sm text-gray-900': {},
        },
      });
      
      // Admin-specific components
      addComponents({
        '.sidebar-nav': {
          '@apply flex flex-col space-y-1': {},
        },
        '.sidebar-nav-item': {
          '@apply flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors duration-150': {},
        },
        '.sidebar-nav-item-active': {
          '@apply bg-blue-100 text-blue-700': {},
        },
        '.sidebar-nav-item-inactive': {
          '@apply text-gray-600 hover:bg-gray-50 hover:text-gray-900': {},
        },
      });
    },
  ],
  
  // Disable preflight to avoid conflicts with existing styles
  corePlugins: {
    preflight: false,
  },
  
  // Optimize for production
  ...(process.env.NODE_ENV === 'production' && {
    purge: {
      enabled: true,
      content: [
        "../../../Templates/**/*.html",
        "../../../class/**/*.py",
        "../../../static/**/*.js",
      ],
      options: {
        safelist: [
          // Keep dynamic classes that might be generated
          /^bg-/,
          /^text-/,
          /^border-/,
          /^hover:/,
          /^focus:/,
          /^active:/,
          'material-symbols-outlined',
        ],
      },
    },
  }),
}
