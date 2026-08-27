import { useTheme } from '../../context/ThemeContext'
import { Sun, Moon } from 'lucide-react'

export default function ThemeToggle({ style = {}, className = '', showLabel = false }) {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`theme-toggle-btn ${className}`}
      title={isDark ? 'Switch to Light Mode (☀️)' : 'Switch to Dark Mode (🌙)'}
      aria-label={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
      style={{
        display:        'inline-flex',
        alignItems:     'center',
        justifyContent: 'center',
        gap:            '8px',
        padding:        showLabel ? '6px 12px' : '8px',
        borderRadius:   'var(--radius)',
        border:         '1px solid var(--gray-300)',
        background:     'var(--card-bg, #fff)',
        color:          'var(--gray-700)',
        cursor:         'pointer',
        transition:     'all 0.2s ease',
        fontSize:       '14px',
        fontWeight:     500,
        boxShadow:      'var(--shadow)',
        ...style,
      }}
    >
      <span style={{ display: 'inline-flex', alignItems: 'center', fontSize: '16px', lineHeight: 1 }}>
        {isDark ? '☀️' : '🌙'}
      </span>
      {showLabel && (
        <span>{isDark ? 'Light Mode' : 'Dark Mode'}</span>
      )}
    </button>
  )
}
