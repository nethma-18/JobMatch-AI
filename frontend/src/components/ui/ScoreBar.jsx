export default function ScoreBar({ score, max = 100, label, showValue = true }) {
  const pct = Math.min((score / max) * 100, 100)
  const color =
    pct >= 70 ? 'var(--success)' :
    pct >= 45 ? 'var(--warning)' :
    'var(--danger)'

  return (
    <div style={{ width: '100%' }}>
      {(label || showValue) && (
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          {label && <span style={{ fontSize: 13, color: 'var(--gray-600)' }}>{label}</span>}
          {showValue && (
            <span style={{ fontSize: 13, fontWeight: 600, color }}>{Math.round(score)}</span>
          )}
        </div>
      )}
      <div style={{
        height: 8,
        background: 'var(--gray-200)',
        borderRadius: 999,
        overflow: 'hidden',
      }}>
        <div style={{
          height:     '100%',
          width:      `${pct}%`,
          background: color,
          borderRadius: 999,
          transition: 'width 0.6s ease',
        }} />
      </div>
    </div>
  )
}