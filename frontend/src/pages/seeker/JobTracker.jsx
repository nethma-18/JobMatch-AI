import { useState, useEffect } from 'react'
import { seekerAPI } from '../../api/seeker'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Badge from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import { statusBadge, fmtDate } from '../../utils/helpers'
import { Plus, Trash2, Edit2, ExternalLink } from 'lucide-react'

const STATUSES = ['applied', 'interview', 'offer', 'rejected', 'withdrawn']

const EMPTY_FORM = {
  job_title: '', company: '', job_url: '',
  status: 'applied', notes: '', location: '',
  salary_expected: '', contact_person: '',
}

export default function JobTracker() {
  const [apps, setApps]         = useState([])
  const [stats, setStats]       = useState({})
  const [loading, setLoading]   = useState(true)
  const [modalOpen, setModal]   = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [form, setForm]         = useState(EMPTY_FORM)
  const [saving, setSaving]     = useState(false)
  const [filterStatus, setFilter] = useState('all')
  const [view, setView]         = useState('board')  // board | list

  const load = async () => {
    try {
      const [a, s] = await Promise.all([
        seekerAPI.getApplications(),
        seekerAPI.getStats(),
      ])
      setApps(a.data.applications || [])
      setStats(s.data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const openNew = () => {
    setEditItem(null)
    setForm(EMPTY_FORM)
    setModal(true)
  }

  const openEdit = (item) => {
    setEditItem(item)
    setForm({
      job_title:       item.job_title   || '',
      company:         item.company     || '',
      job_url:         item.job_url     || '',
      status:          item.status      || 'applied',
      notes:           item.notes       || '',
      location:        item.location    || '',
      salary_expected: item.salary_expected || '',
      contact_person:  item.contact_person  || '',
    })
    setModal(true)
  }

  const handleSave = async () => {
    if (!form.job_title || !form.company) {
      toast.error('Job title and company are required')
      return
    }
    setSaving(true)
    try {
      if (editItem) {
        await seekerAPI.updateApplication(editItem.id, form)
        toast.success('Application updated')
      } else {
        await seekerAPI.createApplication(form)
        toast.success('Application added!')
      }
      setModal(false)
      load()
    } catch {
      toast.error('Save failed')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this application?')) return
    try {
      await seekerAPI.deleteApplication(id)
      toast.success('Deleted')
      load()
    } catch {
      toast.error('Delete failed')
    }
  }

  const handleStatusChange = async (id, newStatus) => {
    try {
      await seekerAPI.updateApplication(id, { status: newStatus })
      load()
    } catch {
      toast.error('Update failed')
    }
  }

  const selectStyle = {
    padding: '7px 10px', border: '1px solid var(--gray-300)',
    borderRadius: 8, fontSize: 13, background: '#fff', cursor: 'pointer',
  }

  const filtered = filterStatus === 'all'
    ? apps
    : apps.filter((a) => a.status === filterStatus)

  // Board view: group by status
  const columns = STATUSES.map((s) => ({
    status: s,
    items:  apps.filter((a) => a.status === s),
  }))

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Job Tracker</h1>
          <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>Track all your job applications</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={() => setView('board')} style={{
            padding: '7px 14px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: view === 'board' ? 'var(--primary)' : 'var(--gray-100)',
            color: view === 'board' ? '#fff' : 'var(--gray-600)', fontSize: 13,
          }}>Board</button>
          <button onClick={() => setView('list')} style={{
            padding: '7px 14px', borderRadius: 8, border: 'none', cursor: 'pointer',
            background: view === 'list' ? 'var(--primary)' : 'var(--gray-100)',
            color: view === 'list' ? '#fff' : 'var(--gray-600)', fontSize: 13,
          }}>List</button>
          <Button onClick={openNew}><Plus size={15} /> Add Application</Button>
        </div>
      </div>

      {/* Stats bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12, marginBottom: 24 }}>
        {[
          { label: 'Total',     value: stats.total    || 0, color: 'var(--gray-700)' },
          { label: 'Applied',   value: stats.applied  || 0, color: 'var(--info)'     },
          { label: 'Interview', value: stats.interview || 0, color: 'var(--warning)'  },
          { label: 'Offers',    value: stats.offer    || 0, color: 'var(--success)'   },
          { label: 'Rejected',  value: stats.rejected  || 0, color: 'var(--danger)'   },
        ].map((s) => (
          <Card key={s.label} padding="16px" style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 26, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 2 }}>{s.label}</div>
          </Card>
        ))}
      </div>

      {/* Board view */}
      {view === 'board' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, overflowX: 'auto' }}>
          {columns.map(({ status, items }) => (
            <div key={status}>
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                marginBottom: 10,
              }}>
                <span style={{ fontWeight: 600, fontSize: 13, textTransform: 'capitalize' }}>{status}</span>
                <Badge variant={statusBadge(status)}>{items.length}</Badge>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {items.map((app) => (
                  <Card key={app.id} padding="14px" style={{ cursor: 'pointer' }}>
                    <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 3 }}>{app.job_title}</div>
                    <div style={{ fontSize: 12, color: 'var(--gray-500)', marginBottom: 8 }}>{app.company}</div>
                    <div style={{ fontSize: 11, color: 'var(--gray-400)', marginBottom: 10 }}>
                      {fmtDate(app.applied_date)}
                    </div>
                    <div style={{ display: 'flex', gap: 4 }}>
                      <button onClick={() => openEdit(app)} style={{
                        flex: 1, padding: '4px', border: '1px solid var(--gray-200)',
                        borderRadius: 6, background: '#fff', cursor: 'pointer', fontSize: 11,
                      }}>
                        <Edit2 size={11} />
                      </button>
                      <button onClick={() => handleDelete(app.id)} style={{
                        flex: 1, padding: '4px', border: '1px solid #fecaca',
                        borderRadius: 6, background: '#fff7f7', cursor: 'pointer', fontSize: 11,
                        color: 'var(--danger)',
                      }}>
                        <Trash2 size={11} />
                      </button>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* List view */}
      {view === 'list' && (
        <>
          <div style={{ display: 'flex', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
            {['all', ...STATUSES].map((s) => (
              <button key={s} onClick={() => setFilter(s)} style={{
                padding: '5px 14px', borderRadius: 999, border: 'none',
                cursor: 'pointer', fontSize: 12, textTransform: 'capitalize',
                background: filterStatus === s ? 'var(--primary)' : 'var(--gray-100)',
                color: filterStatus === s ? '#fff' : 'var(--gray-600)',
              }}>{s}</button>
            ))}
          </div>

          <Card padding="0">
            {filtered.length === 0 ? (
              <div style={{ padding: 32, textAlign: 'center', color: 'var(--gray-400)' }}>
                No applications found
              </div>
            ) : filtered.map((app, i) => (
              <div key={app.id} style={{
                display: 'flex', alignItems: 'center', gap: 16,
                padding: '14px 20px',
                borderBottom: i < filtered.length - 1 ? '1px solid var(--gray-100)' : 'none',
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{app.job_title}</div>
                  <div style={{ fontSize: 13, color: 'var(--gray-500)' }}>{app.company}</div>
                  {app.location && (
                    <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>{app.location}</div>
                  )}
                </div>
                <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>{fmtDate(app.applied_date)}</div>
                <select
                  value={app.status}
                  onChange={(e) => handleStatusChange(app.id, e.target.value)}
                  style={selectStyle}
                >
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                <Badge variant={statusBadge(app.status)}>{app.status}</Badge>
                {app.job_url && (
                  <a href={app.job_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink size={15} color="var(--gray-400)" />
                  </a>
                )}
                <button onClick={() => openEdit(app)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                  <Edit2 size={15} color="var(--gray-400)" />
                </button>
                <button onClick={() => handleDelete(app.id)} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
                  <Trash2 size={15} color="var(--danger)" />
                </button>
              </div>
            ))}
          </Card>
        </>
      )}

      {/* Add / Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModal(false)}
        title={editItem ? 'Edit Application' : 'Add Application'}
        width={520}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Input
            label="Job Title" required
            value={form.job_title}
            onChange={(e) => setForm((p) => ({ ...p, job_title: e.target.value }))}
            placeholder="Software Engineer"
          />
          <Input
            label="Company" required
            value={form.company}
            onChange={(e) => setForm((p) => ({ ...p, company: e.target.value }))}
            placeholder="Acme Corp"
          />
          <Input
            label="Job URL"
            value={form.job_url}
            onChange={(e) => setForm((p) => ({ ...p, job_url: e.target.value }))}
            placeholder="https://..."
          />
          <Input
            label="Location"
            value={form.location}
            onChange={(e) => setForm((p) => ({ ...p, location: e.target.value }))}
            placeholder="Remote / Colombo"
          />

          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 4 }}>
              Status
            </label>
            <select
              value={form.status}
              onChange={(e) => setForm((p) => ({ ...p, status: e.target.value }))}
              style={{
                width: '100%', padding: '9px 12px',
                border: '1px solid var(--gray-300)',
                borderRadius: 'var(--radius)', fontSize: 14, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)',
              }}
            >
              {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>

          <Input
            label="Notes"
            name="notes" rows={3}
            value={form.notes}
            onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))}
            placeholder="Any notes about this application..."
          />

          <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
            <Button variant="secondary" fullWidth onClick={() => setModal(false)}>
              Cancel
            </Button>
            <Button fullWidth onClick={handleSave} loading={saving}>
              {editItem ? 'Save Changes' : 'Add Application'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}