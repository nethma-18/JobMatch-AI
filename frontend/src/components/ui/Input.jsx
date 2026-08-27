export default function Input({
  label,
  name,
  type = 'text',
  placeholder,
  value,
  onChange,
  error,
  required,
  disabled,
  style = {},
  rows,
}) {
  const inputStyle = {
    width:        '100%',
    padding:      '9px 12px',
    border:       `1px solid ${error ? 'var(--danger)' : 'var(--gray-300)'}`,
    borderRadius: 'var(--radius)',
    fontSize:     '14px',
    outline:      'none',
    transition:   'border-color 0.15s, background-color 0.3s ease, color 0.3s ease',
    background:   disabled ? 'var(--gray-100)' : 'var(--input-bg, #fff)',
    color:        'var(--gray-800)',
    ...style,
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
      {label && (
        <label style={{ fontSize: '13px', fontWeight: 500, color: 'var(--gray-700)' }}>
          {label} {required && <span style={{ color: 'var(--danger)' }}>*</span>}
        </label>
      )}
      {rows ? (
        <textarea
          name={name}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          disabled={disabled}
          rows={rows}
          style={{ ...inputStyle, resize: 'vertical', lineHeight: 1.5 }}
        />
      ) : (
        <input
          type={type}
          name={name}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          disabled={disabled}
          style={inputStyle}
        />
      )}
      {error && (
        <span style={{ fontSize: '12px', color: 'var(--danger)' }}>{error}</span>
      )}
    </div>
  )
}