const colors = {
  success:  { bg: '#dcfce7', color: '#15803d' },
  danger:   { bg: '#fee2e2', color: '#b91c1c' },
  warning:  { bg: '#fef9c3', color: '#92400e' },
  info:     { bg: '#dbeafe', color: '#1d4ed8' },
  purple:   { bg: '#ede9fe', color: '#6d28d9' },
  gray:     { bg: '#f3f4f6', color: '#4b5563' },
}

export default function Badge({ children, variant = 'gray', style = {} }) {
  const c = colors[variant] || colors.gray
  return (
    <span style={{
      display:      'inline-flex',
      alignItems:   'center',
      padding:      '2px 10px',
      borderRadius: '999px',
      fontSize:     '11px',
      fontWeight:   600,
      letterSpacing: '0.02em',
      background:   c.bg,
      color:        c.color,
      ...style,
    }}>
      {children}
    </span>
  )
}