import Spinner from './Spinner'
import clsx from 'clsx'

const styles = {
  base: {
    display:        'inline-flex',
    alignItems:     'center',
    justifyContent: 'center',
    gap:            '8px',
    padding:        '9px 18px',
    borderRadius:   'var(--radius)',
    fontWeight:     600,
    fontSize:       '14px',
    border:         'none',
    transition:     'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
    cursor:         'pointer',
    letterSpacing:  '0.01em',
  },
  primary: {
    background: 'var(--accent-gradient, var(--primary))',
    color:      '#ffffff',
    boxShadow:  '0 4px 14px rgba(99, 102, 241, 0.35)',
  },
  secondary: {
    background: 'var(--card-bg, var(--gray-100))',
    color:      'var(--gray-700)',
    border:     '1px solid var(--card-border, var(--gray-300))',
  },
  danger: {
    background: 'var(--danger)',
    color:      '#ffffff',
  },
  ghost: {
    background: 'transparent',
    color:      'var(--primary)',
  },
  sm: { padding: '6px 12px', fontSize: '12px' },
  lg: { padding: '12px 24px', fontSize: '15px' },
}

export default function Button({
  children,
  variant = 'primary',
  size,
  loading = false,
  disabled = false,
  onClick,
  type = 'button',
  style = {},
  fullWidth = false,
  pill = false,
}) {
  const combined = {
    ...styles.base,
    ...styles[variant],
    ...(size ? styles[size] : {}),
    ...(pill ? { borderRadius: '999px' } : {}),
    ...(fullWidth ? { width: '100%' } : {}),
    ...(disabled || loading ? { opacity: 0.6, cursor: 'not-allowed' } : {}),
    ...style,
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || loading}
      style={combined}
    >
      {loading && <Spinner size={14} color={variant === 'primary' ? '#fff' : 'var(--primary)'} />}
      {children}
    </button>
  )
}