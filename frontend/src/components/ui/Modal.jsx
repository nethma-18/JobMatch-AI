import { X } from 'lucide-react'

export default function Modal({ open, onClose, title, children, width = 520 }) {
  if (!open) return null
  return (
    <div
      onClick={onClose}
      style={{
        position:       'fixed',
        inset:          0,
        background:     'rgba(0,0,0,0.35)',
        zIndex:         1000,
        display:        'flex',
        alignItems:     'center',
        justifyContent: 'center',
        padding:        16,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          background:   'var(--card-bg, #fff)',
          color:        'var(--gray-800)',
          borderRadius: 'var(--radius)',
          width:        '100%',
          maxWidth:     width,
          maxHeight:    '90vh',
          overflowY:    'auto',
          boxShadow:    '0 20px 60px rgba(0,0,0,0.3)',
          border:       '1px solid var(--card-border, var(--gray-200))',
          transition:   'background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease',
        }}
      >
        {/* Header */}
        <div style={{
          display:        'flex',
          justifyContent: 'space-between',
          alignItems:     'center',
          padding:        '16px 20px',
          borderBottom:   '1px solid var(--card-border, var(--gray-200))',
        }}>
          <h3 style={{ fontWeight: 600, fontSize: 16 }}>{title}</h3>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}
          >
            <X size={18} color="var(--gray-500)" />
          </button>
        </div>
        {/* Body */}
        <div style={{ padding: 20 }}>{children}</div>
      </div>
    </div>
  )
}