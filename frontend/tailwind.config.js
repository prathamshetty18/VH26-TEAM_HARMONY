/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          'Inter',
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          'sans-serif',
        ],
        mono: [
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Monaco',
          'Consolas',
          '"Liberation Mono"',
          '"Courier New"',
          'monospace',
        ],
      },
      colors: {
        hmi: {
          bg: '#f8fafc',
          panel: '#ffffff',
          sidebar: '#f8fafc',
          border: '#e2e8f0',
          borderDark: '#cbd5e1',
          header: '#ffffff',
          text: '#0f172a',
          muted: '#64748b',
          subtle: '#94a3b8',
        }
      }
    },
  },
  plugins: [],
}
