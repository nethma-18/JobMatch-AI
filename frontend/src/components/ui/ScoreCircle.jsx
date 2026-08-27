export default function ScoreCircle({ score = 0, size = 100, strokeWidth = 8, label = 'AI Match' }) {
  const pct = Math.min(Math.max(score, 0), 100)
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const strokeDashoffset = circumference - (pct / 100) * circumference

  const color =
    pct >= 75 ? '#10b981' :
    pct >= 50 ? '#f59e0b' :
    '#ef4444'

  return (
    <div style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
      <div style={{ position: 'relative', width: size, height: size, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke="var(--gray-200)"
            strokeWidth={strokeWidth}
            fill="transparent"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={color}
            strokeWidth={strokeWidth}
            fill="transparent"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)' }}
          />
        </svg>
        <div style={{ position: 'absolute', textAlign: 'center' }}>
          <span style={{ fontSize: size * 0.26, fontWeight: 700, color: 'var(--gray-900)' }}>
            {Math.round(pct)}%
          </span>
        </div>
      </div>
      {label && (
        <span style={{ fontSize: 12, fontWeight: 500, color: 'var(--gray-500)' }}>
          {label}
        </span>
      )}
    </div>
  )
}
