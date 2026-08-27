export const fmtDate = (date) => {
  if (!date) return '—'
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export const fmtScore = (score) =>
  score !== null && score !== undefined ? `${Math.round(score)}%` : '—'

export const scoreColor = (score) =>
  score >= 70 ? 'var(--success)' :
  score >= 45 ? 'var(--warning)' :
  'var(--danger)'

export const statusBadge = (status) => {
  const map = {
    applied:   'info',
    interview: 'purple',
    offer:     'success',
    rejected:  'danger',
    withdrawn: 'gray',
    open:      'success',
    closed:    'danger',
    draft:     'gray',
    pending:   'warning',
    confirmed: 'success',
    completed: 'info',
    cancelled: 'danger',
  }
  return map[status] || 'gray'
}

export const downloadCSV = (blob, filename) => {
  const url = URL.createObjectURL(blob)
  const a   = document.createElement('a')
  a.href    = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

export const truncate = (str, n = 60) =>
  str && str.length > n ? str.slice(0, n) + '...' : str