export default function Card({ children, style = {}, padding = '24px', shadow = true, hoverable = false, className = '', onClick }) {
  return (
    <div
      onClick={onClick}
      className={`${hoverable ? 'spotify-card' : ''} ${className}`}
      style={{
        background:   'var(--card-bg, #fff)',
        borderRadius: 'var(--radius)',
        padding,
        boxShadow:    shadow ? 'var(--shadow)' : 'none',
        border:       '1px solid var(--card-border, var(--gray-200))',
        color:        'var(--gray-800)',
        transition:   'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
        ...style,
      }}
    >
      {children}
    </div>
  )
}