export default function Spinner({ size = 24, color = 'var(--primary)' }) {
  return (
    <div style={{
      width:  size,
      height: size,
      border: `2px solid var(--gray-200)`,
      borderTop: `2px solid ${color}`,
      borderRadius: '50%',
      animation: 'spin 0.7s linear infinite',
    }} />
  )
}

// Add to index.css:
// @keyframes spin { to { transform: rotate(360deg); } }