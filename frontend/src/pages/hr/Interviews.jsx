import { useState, useEffect } from 'react'
import { hrAPI } from '../../api/hr'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import { statusBadge, fmtDate } from '../../utils/helpers'
import { Calendar, Plus, ExternalLink } from 'lucide-react'

export default function Interviews() {
  const [interviews, setInterviews] = useState([])
  const [upcoming, setUpcoming]     = useState([])
  const [jobs, setJobs]             = useState([])
  const [rankings, setRankings]     = useState([])
  const [modalOpen, setModal]       = useState(false)
  const [loading, setLoading]       = useState(true)
  const [saving, setSaving]         = useState(false)
  const [selectedJob, setSelectedJob] = useState('')
  const [form, setForm] = useState({
    candidate_id: '', job_id: '', scheduled_date: '',
    duration_minutes: 60, meeting_link: '', notes: '',
  })

  const load = async () => {
    setLoading(true)
    try {
      const [iv, up, j] = await Promise.all([
        hrAPI.getInterviews({}),
        hrAPI.getUpcoming(),
        hrAPI.getJobs({ status: 'open' }),
      ])
      setInterviews(iv.data || [])
      setUpcoming(up.data || [])
      setJobs(j.data.jobs || [])
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  useEffect(() => {
    if (!selectedJob) return
    hrAPI.getRankings(selectedJob)
      .then((r) => setRankings(r.data?.rankings || []))
      .catch(() => setRankings([]))
  }, [selectedJob])

  const openModal = () => {
    setForm({ candidate_id: '', job_id: '', scheduled_date: '', duration_minutes: 60, meeting_link: '', notes: '' })
    setModal(true)
  }

  const handleSave = async () => {
    if (!form.candidate_id || !form.scheduled_date) {
      toast.error('Candidate and date are required')
      return
    }
    setSaving(true)
    try {
      await hrAPI.scheduleInterview({
        ...form,
        job_id: selectedJob || null,
        scheduled_date: new Date(form.scheduled_date).toISOString(),
        duration_minutes: Number(form.duration_minutes),
      })
      toast.success('Interview scheduled!')
      setModal(false)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Schedule failed')
    } finally { setSaving(false) }
  }

  const handleStatusUpdate = async (id, status) => {
    try {
      await hrAPI.updateInterview(id, { status })
      toast.success(`Status updated to ${status}`)
      load()
    } catch { toast.error('Update failed') }
  }

  const selectStyle = {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--gray-300)',
    borderRadius: 10, fontSize: 14, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)',
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Interview Scheduler</h1>
          <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>Schedule and track candidate interviews</p>
        </div>
        <Button onClick={openModal}><Plus size={15} /> Schedule Interview</Button>
      </div>

      {/* Upcoming */}
      {upcoming.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>
            Upcoming (next 7 days)
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12 }}>
            {upcoming.map((iv) => (
              <Card key={iv.id} padding="16px" style={{ borderLeft: '3px solid var(--primary)' }}>
                <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>
                  {fmtDate(iv.scheduled_date)}
                </div>
                <div style={{ fontSize: 12, color: 'var(--gray-500)', marginBottom: 8 }}>
                  {iv.duration_minutes} min
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Badge variant={statusBadge(iv.status)}>{iv.status}</Badge>
                  {iv.calendar_link && (
                    <a href={iv.calendar_link} target="_blank" rel="noopener noreferrer">
                      <ExternalLink size={13} color="var(--primary)" />
                    </a>
                  )}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* All interviews */}
      <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>All Interviews</h2>
      <Card padding="0">
        {loading ? (
          <p style={{ padding: 24, textAlign: 'center', color: 'var(--gray-400)' }}>Loading...</p>
        ) : interviews.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center' }}>
            <Calendar size={36} color="var(--gray-300)" style={{ marginBottom: 12 }} />
            <p style={{ color: 'var(--gray-400)', fontSize: 13 }}>No interviews scheduled yet</p>
          </div>
        ) : interviews.map((iv, i) => (
          <div key={iv.id} style={{
            display: 'flex', alignItems: 'center', gap: 16,
            padding: '14px 20px',
            borderBottom: i < interviews.length - 1 ? '1px solid var(--gray-100)' : 'none',
          }}>
            <Calendar size={18} color="var(--primary)" style={{ flexShrink: 0 }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 500 }}>{fmtDate(iv.scheduled_date)}</div>
              <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 1 }}>
                {iv.duration_minutes} min
                {iv.meeting_link ? ` · ${iv.meeting_link.slice(0, 30)}...` : ''}
              </div>
            </div>
            <Badge variant={statusBadge(iv.status)}>{iv.status}</Badge>
            {iv.calendar_link && (
              <a href={iv.calendar_link} target="_blank" rel="noopener noreferrer">
                <Button variant="ghost" size="sm"><ExternalLink size={13} /> Calendar</Button>
              </a>
            )}
            <select
              value={iv.status}
              onChange={(e) => handleStatusUpdate(iv.id, e.target.value)}
              style={{ ...selectStyle, width: 140 }}
            >
              {['pending','confirmed','completed','cancelled','rescheduled'].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        ))}
      </Card>

      {/* Schedule Modal */}
      <Modal open={modalOpen} onClose={() => setModal(false)} title="Schedule Interview" width={520}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 6 }}>
              Job Post
            </label>
            <select
              value={selectedJob}
              onChange={(e) => setSelectedJob(e.target.value)}
              style={selectStyle}
            >
              <option value="">-- Select job (optional) --</option>
              {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
            </select>
          </div>

          {rankings.length > 0 && (
            <div>
              <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 6 }}>
                Candidate *
              </label>
              <select
                value={form.candidate_id}
                onChange={(e) => setForm((p) => ({ ...p, candidate_id: e.target.value }))}
                style={selectStyle}
              >
                <option value="">-- Select candidate --</option>
                {rankings.map((r) => (
                  <option key={r.resume_id} value={r.resume_id}>
                    {r.candidate_name || r.filename} — {Math.round(r.score)}%
                  </option>
                ))}
              </select>
            </div>
          )}

          {!selectedJob && (
            <Input
              label="Candidate ID (if no job selected)"
              value={form.candidate_id}
              onChange={(e) => setForm((p) => ({ ...p, candidate_id: e.target.value }))}
              placeholder="Resume ID"
            />
          )}

          <Input
            label="Date & Time *" type="datetime-local"
            value={form.scheduled_date}
            onChange={(e) => setForm((p) => ({ ...p, scheduled_date: e.target.value }))}
          />
          <Input
            label="Duration (minutes)"
            type="number"
            value={form.duration_minutes}
            onChange={(e) => setForm((p) => ({ ...p, duration_minutes: e.target.value }))}
          />
          <Input
            label="Meeting Link (optional)"
            value={form.meeting_link}
            onChange={(e) => setForm((p) => ({ ...p, meeting_link: e.target.value }))}
            placeholder="https://meet.google.com/..."
          />
          <Input
            label="Notes (optional)" rows={3}
            value={form.notes}
            onChange={(e) => setForm((p) => ({ ...p, notes: e.target.value }))}
          />
          <div style={{ display: 'flex', gap: 10 }}>
            <Button variant="secondary" fullWidth onClick={() => setModal(false)}>Cancel</Button>
            <Button fullWidth onClick={handleSave} loading={saving}>Schedule Interview</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}