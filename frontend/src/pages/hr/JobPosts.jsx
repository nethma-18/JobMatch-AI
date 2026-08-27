import { useState, useEffect } from 'react'
import { hrAPI } from '../../api/hr'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Badge from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import { statusBadge, fmtDate } from '../../utils/helpers'
import { Plus, Edit2, Trash2, Copy, Briefcase, MapPin, DollarSign } from 'lucide-react'

const EMPTY = {
  title: '', description: '', required_skills: '', preferred_skills: '',
  experience_required: '', location: '',
  salary_min: '', salary_max: '', is_template: false,
  education_required: '', employment_type: '', status: 'open',
}

export default function JobPosts() {
  const [jobs, setJobs]         = useState([])
  const [total, setTotal]       = useState(0)
  const [loading, setLoading]   = useState(true)
  const [modalOpen, setModal]   = useState(false)
  const [editItem, setEditItem] = useState(null)
  const [form, setForm]         = useState(EMPTY)
  const [saving, setSaving]     = useState(false)
  const [filterStatus, setFilter] = useState('')
  const [showTemplates, setShowTemplates] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const params = {}
      if (filterStatus)   params.status      = filterStatus
      if (showTemplates)  params.is_template = true
      const res = await hrAPI.getJobs(params)
      setJobs(res.data.jobs || [])
      setTotal(res.data.total || 0)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [filterStatus, showTemplates])

  const openNew = () => {
    setEditItem(null)
    setForm(EMPTY)
    setModal(true)
  }

  const openEdit = (job) => {
    setEditItem(job)
    setForm({
      title:               job.title || '',
      description:         job.description_text || '',
      required_skills:     (job.required_skills || []).join(', '),
      preferred_skills:    (job.preferred_skills || []).join(', '),
      experience_required: job.experience_required || '',
      location:            job.location || '',
      salary_min:          job.salary_range?.min || '',
      salary_max:          job.salary_range?.max || '',
      is_template:         job.is_template || false,
      education_required:  job.education_required || '',
      employment_type:     job.employment_type || '',
      status:              job.status || 'open',
    })
    setModal(true)
  }

  const handleSave = async () => {
    if (!form.title || !form.description) {
      toast.error('Title and description are required')
      return
    }
    setSaving(true)
    try {
      const payload = {
        title:               form.title,
        description:         form.description,
        required_skills:     form.required_skills
          ? form.required_skills.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
        preferred_skills:    form.preferred_skills
          ? form.preferred_skills.split(',').map((s) => s.trim()).filter(Boolean)
          : [],
        experience_required: form.experience_required ? Number(form.experience_required) : null,
        location:            form.location,
        salary_min:          form.salary_min ? Number(form.salary_min) : null,
        salary_max:          form.salary_max ? Number(form.salary_max) : null,
        is_template:         form.is_template,
        education_required:  form.education_required || null,
        employment_type:     form.employment_type || null,
        status:              form.status || 'open',
      }

      if (editItem) {
        await hrAPI.updateJob(editItem.id, payload)
        toast.success('Job updated')
      } else {
        await hrAPI.createJob(payload)
        toast.success('Job created!')
      }
      setModal(false)
      load()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this job post?')) return
    try {
      await hrAPI.deleteJob(id)
      toast.success('Deleted')
      load()
    } catch { toast.error('Delete failed') }
  }

  const handleDuplicate = async (id) => {
    try {
      await hrAPI.duplicateJob(id)
      toast.success('Job duplicated')
      load()
    } catch { toast.error('Duplicate failed') }
  }

  const handleStatusToggle = async (job) => {
    const newStatus = job.status === 'open' ? 'closed' : 'open'
    try {
      await hrAPI.updateJob(job.id, { status: newStatus })
      load()
    } catch { toast.error('Update failed') }
  }

  const selectStyle = {
    padding: '8px 12px', border: '1px solid var(--gray-300)',
    borderRadius: 8, fontSize: 13, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)', cursor: 'pointer',
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Job Posts</h1>
          <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>{total} total posts</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <select value={filterStatus} onChange={(e) => setFilter(e.target.value)} style={selectStyle}>
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="closed">Closed</option>
            <option value="draft">Draft</option>
          </select>
          <button
            onClick={() => setShowTemplates((p) => !p)}
            style={{
              padding: '8px 14px', borderRadius: 8, fontSize: 13,
              border: `2px solid ${showTemplates ? 'var(--primary)' : 'var(--gray-200)'}`,
              background: showTemplates ? 'var(--primary-light)' : '#fff',
              color: showTemplates ? 'var(--primary)' : 'var(--gray-600)', cursor: 'pointer',
            }}
          >
            Templates
          </button>
          <Button onClick={openNew}><Plus size={15} /> New Job</Button>
        </div>
      </div>

      {/* Job cards */}
      {loading ? (
        <p style={{ color: 'var(--gray-400)', textAlign: 'center', padding: 40 }}>Loading...</p>
      ) : jobs.length === 0 ? (
        <Card style={{ textAlign: 'center', padding: 48 }}>
          <Briefcase size={40} color="var(--gray-300)" style={{ marginBottom: 12 }} />
          <p style={{ color: 'var(--gray-400)' }}>No job posts yet. Create your first one.</p>
          <Button onClick={openNew} style={{ marginTop: 16 }}><Plus size={15} /> Create Job Post</Button>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {jobs.map((job) => (
            <Card key={job.id}>
              <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 16 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <h3 style={{ fontWeight: 600, fontSize: 15 }}>{job.title}</h3>
                    <Badge variant={statusBadge(job.status)}>{job.status}</Badge>
                    {job.is_template && <Badge variant="purple">Template</Badge>}
                  </div>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, marginBottom: 10 }}>
                    {job.location && (
                      <span style={{ fontSize: 12, color: 'var(--gray-500)', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <MapPin size={12} /> {job.location}
                      </span>
                    )}
                    {job.experience_required && (
                      <span style={{ fontSize: 12, color: 'var(--gray-500)' }}>
                        {job.experience_required}+ years exp
                      </span>
                    )}
                    {job.education_required && (
                      <span style={{ fontSize: 12, color: 'var(--gray-500)' }}>
                        🎓 {job.education_required}
                      </span>
                    )}
                    {job.employment_type && (
                      <span style={{ fontSize: 12, color: 'var(--gray-500)' }}>
                        💼 {job.employment_type}
                      </span>
                    )}
                    {job.salary_range?.min && (
                      <span style={{ fontSize: 12, color: 'var(--gray-500)', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <DollarSign size={12} /> {job.salary_range.min.toLocaleString()} – {job.salary_range.max?.toLocaleString()}
                      </span>
                    )}
                    <span style={{ fontSize: 12, color: 'var(--gray-400)' }}>
                      Created {fmtDate(job.created_at)}
                    </span>
                  </div>

                  <p style={{ fontSize: 13, color: 'var(--gray-600)', lineHeight: 1.5, marginBottom: 10 }}>
                    {job.description_text?.slice(0, 160)}...
                  </p>

                  {job.required_skills?.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 6 }}>
                      <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--gray-600)', alignSelf: 'center', marginRight: 4 }}>Required:</span>
                      {job.required_skills.slice(0, 8).map((s) => (
                        <Badge key={s} variant="info" style={{ fontSize: 10 }}>{s}</Badge>
                      ))}
                      {job.required_skills.length > 8 && (
                        <Badge variant="gray" style={{ fontSize: 10 }}>+{job.required_skills.length - 8}</Badge>
                      )}
                    </div>
                  )}

                  {job.preferred_skills?.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                      <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--gray-600)', alignSelf: 'center', marginRight: 4 }}>Preferred:</span>
                      {job.preferred_skills.slice(0, 8).map((s) => (
                        <Badge key={s} variant="success" style={{ fontSize: 10 }}>{s}</Badge>
                      ))}
                      {job.preferred_skills.length > 8 && (
                        <Badge variant="gray" style={{ fontSize: 10 }}>+{job.preferred_skills.length - 8}</Badge>
                      )}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flexShrink: 0 }}>
                  <Button size="sm" variant="secondary" onClick={() => openEdit(job)}>
                    <Edit2 size={13} /> Edit
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => handleDuplicate(job.id)}>
                    <Copy size={13} /> Duplicate
                  </Button>
                  <Button
                    size="sm"
                    variant={job.status === 'open' ? 'secondary' : 'primary'}
                    onClick={() => handleStatusToggle(job)}
                  >
                    {job.status === 'open' ? 'Close' : 'Reopen'}
                  </Button>
                  <Button size="sm" variant="danger" onClick={() => handleDelete(job.id)}>
                    <Trash2 size={13} /> Delete
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal
        open={modalOpen}
        onClose={() => setModal(false)}
        title={editItem ? 'Edit Job Post' : 'Create Job Post'}
        width={620}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Input
            label="Job Title" required
            value={form.title}
            onChange={(e) => setForm((p) => ({ ...p, title: e.target.value }))}
            placeholder="Senior React Developer"
          />
          <Input
            label="Job Description" required rows={6}
            value={form.description}
            onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
            placeholder="Describe the role, responsibilities, and requirements..."
          />
          <Input
            label="Required Skills (comma-separated)"
            value={form.required_skills}
            onChange={(e) => setForm((p) => ({ ...p, required_skills: e.target.value }))}
            placeholder="React, Node.js, MongoDB, AWS"
          />
          <Input
            label="Preferred Skills (comma-separated)"
            value={form.preferred_skills}
            onChange={(e) => setForm((p) => ({ ...p, preferred_skills: e.target.value }))}
            placeholder="TypeScript, Docker, Next.js"
          />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)' }}>Education Required</label>
              <select
                value={form.education_required}
                onChange={(e) => setForm((p) => ({ ...p, education_required: e.target.value }))}
                style={{ ...selectStyle, height: 38 }}
              >
                <option value="">No specific requirement (auto-detect)</option>
                <option value="Associate / Diploma">Associate / Diploma</option>
                <option value="Bachelor's">Bachelor's</option>
                <option value="Master's">Master's</option>
                <option value="PhD">PhD</option>
              </select>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)' }}>Employment Type</label>
              <select
                value={form.employment_type}
                onChange={(e) => setForm((p) => ({ ...p, employment_type: e.target.value }))}
                style={{ ...selectStyle, height: 38 }}
              >
                <option value="">Not specified (auto-detect)</option>
                <option value="Full-time">Full-time</option>
                <option value="Part-time">Part-time</option>
                <option value="Contract">Contract</option>
                <option value="Internship">Internship</option>
              </select>
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Input
              label="Min Experience (years)"
              type="number"
              value={form.experience_required}
              onChange={(e) => setForm((p) => ({ ...p, experience_required: e.target.value }))}
              placeholder="3"
            />
            <Input
              label="Location"
              value={form.location}
              onChange={(e) => setForm((p) => ({ ...p, location: e.target.value }))}
              placeholder="Remote / Colombo"
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Input
              label="Min Salary (USD)"
              type="number"
              value={form.salary_min}
              onChange={(e) => setForm((p) => ({ ...p, salary_min: e.target.value }))}
              placeholder="50000"
            />
            <Input
              label="Max Salary (USD)"
              type="number"
              value={form.salary_max}
              onChange={(e) => setForm((p) => ({ ...p, salary_max: e.target.value }))}
              placeholder="80000"
            />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)' }}>Status</label>
              <select
                value={form.status}
                onChange={(e) => setForm((p) => ({ ...p, status: e.target.value }))}
                style={{ ...selectStyle, height: 38 }}
              >
                <option value="open">Open</option>
                <option value="draft">Draft</option>
                <option value="closed">Closed</option>
              </select>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, cursor: 'pointer', marginTop: 24 }}>
              <input
                type="checkbox"
                checked={form.is_template}
                onChange={(e) => setForm((p) => ({ ...p, is_template: e.target.checked }))}
                style={{ accentColor: 'var(--primary)' }}
              />
              Save as template
            </label>
          </div>
          <div style={{ display: 'flex', gap: 10, marginTop: 4 }}>
            <Button variant="secondary" fullWidth onClick={() => setModal(false)}>Cancel</Button>
            <Button fullWidth onClick={handleSave} loading={saving}>
              {editItem ? 'Save Changes' : 'Create Job Post'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}