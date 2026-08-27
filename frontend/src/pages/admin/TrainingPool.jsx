import { useState, useEffect } from 'react'
import { adminAPI } from '../../api/admin'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Input from '../../components/ui/Input'
import { fmtDate } from '../../utils/helpers'
import { Database, Trash2, RefreshCw, Zap } from 'lucide-react'

export default function TrainingPool() {
  const [items, setItems]     = useState([])
  const [meta, setMeta]       = useState({})
  const [loading, setLoading] = useState(true)
  const [skip, setSkip]       = useState(0)
  const [sourceFilter, setSource] = useState('')
  const [typeFilter, setType]     = useState('')
  const [retraining, setRetraining] = useState(false)
  const [rules, setRules]         = useState(null)
  const [savingRules, setSavingRules] = useState(false)
  const [approveThreshold, setApproveThreshold] = useState(70)
  const [rejectThreshold, setRejectThreshold]   = useState(40)
  const LIMIT = 20

  const load = async () => {
    setLoading(true)
    try {
      const params = { skip, limit: LIMIT }
      if (sourceFilter) params.source    = sourceFilter
      if (typeFilter)   params.data_type = typeFilter
      const res = await adminAPI.getTrainingPool(params)
      setItems(res.data.items || [])
      setMeta(res.data)
    } catch {} finally { setLoading(false) }
  }

  const loadRules = async () => {
    try {
      const res = await adminAPI.getValidationRules()
      setRules(res.data)
      setApproveThreshold(res.data.auto_approve_threshold || 70)
      setRejectThreshold(res.data.auto_reject_threshold   || 40)
    } catch {}
  }

  useEffect(() => { load() }, [skip, sourceFilter, typeFilter])
  useEffect(() => { loadRules() }, [])

  const handleDelete = async (id) => {
    if (!confirm('Remove this document from training pool?')) return
    try {
      await adminAPI.removeFromPool(id)
      toast.success('Removed from training pool')
      load()
    } catch { toast.error('Remove failed') }
  }

  const handleRetrain = async () => {
    if (!confirm('Start model retraining now?')) return
    setRetraining(true)
    try {
      await adminAPI.retrain()
      toast.success('Retraining complete!')
    } catch { toast.error('Retraining failed') }
    finally { setRetraining(false) }
  }

  const handleSaveRules = async () => {
    if (approveThreshold <= rejectThreshold) {
      toast.error('Approve threshold must be higher than reject threshold')
      return
    }
    setSavingRules(true)
    try {
      await adminAPI.updateValidationRules({
        auto_approve_threshold: approveThreshold,
        auto_reject_threshold:  rejectThreshold,
      })
      toast.success('Validation rules updated!')
    } catch { toast.error('Save failed') }
    finally { setSavingRules(false) }
  }

  const sourceColor = (source) =>
    source === 'public_dataset' ? 'info' : 'purple'

  const typeColor = (type) =>
    type === 'resume' ? 'success' :
    type === 'job_description' ? 'warning' : 'gray'

  const selectStyle = {
    padding: '8px 12px', border: '1px solid var(--gray-300)',
    borderRadius: 8, fontSize: 13, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)', cursor: 'pointer',
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Training Pool</h1>
          <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
            Validated data used to train and improve the AI models
          </p>
        </div>
        <Button onClick={handleRetrain} loading={retraining}>
          <Zap size={15} /> Retrain Model
        </Button>
      </div>

      {/* Pool stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 24 }}>
        {[
          { label: 'Total Docs',       value: meta.total                  || 0, color: 'var(--primary)' },
          { label: 'Public Datasets',  value: meta.public_dataset_count   || 0, color: 'var(--info)'    },
          { label: 'User Uploads',     value: meta.user_upload_count      || 0, color: 'var(--purple)'  },
          { label: 'Job Descriptions', value: meta.job_description_count  || 0, color: 'var(--warning)' },
        ].map((s) => (
          <Card key={s.label} padding="18px">
            <div style={{ fontSize: 26, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 4 }}>{s.label}</div>
          </Card>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: 20 }}>
        {/* Pool list */}
        <div>
          {/* Filters */}
          <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
            <select value={sourceFilter} onChange={(e) => setSource(e.target.value)} style={selectStyle}>
              <option value="">All sources</option>
              <option value="public_dataset">Public Dataset</option>
              <option value="user_upload">User Upload</option>
            </select>
            <select value={typeFilter} onChange={(e) => setType(e.target.value)} style={selectStyle}>
              <option value="">All types</option>
              <option value="resume">Resume</option>
              <option value="job_description">Job Description</option>
              <option value="interview_qa">Interview Q&A</option>
            </select>
            <Button variant="secondary" size="sm" onClick={() => { setSource(''); setType(''); setSkip(0) }}>
              <RefreshCw size={13} /> Reset
            </Button>
          </div>

          <Card padding="0">
            {/* Header */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '2fr 120px 100px 100px 80px 50px',
              padding: '10px 18px',
              background: 'var(--gray-50)',
              borderBottom: '1px solid var(--gray-200)',
              fontSize: 12, fontWeight: 600, color: 'var(--gray-500)',
            }}>
              <span>Document</span>
              <span>Source</span>
              <span>Type</span>
              <span>Quality</span>
              <span>Added</span>
              <span></span>
            </div>

            {loading ? (
              <p style={{ padding: 28, textAlign: 'center', color: 'var(--gray-400)' }}>Loading...</p>
            ) : items.length === 0 ? (
              <div style={{ padding: 40, textAlign: 'center' }}>
                <Database size={32} color="var(--gray-300)" style={{ marginBottom: 10 }} />
                <p style={{ color: 'var(--gray-400)', fontSize: 13 }}>No training data found</p>
              </div>
            ) : items.map((item, i) => (
              <div key={item.id} style={{
                display: 'grid',
                gridTemplateColumns: '2fr 120px 100px 100px 80px 50px',
                padding: '11px 18px',
                borderBottom: i < items.length - 1 ? '1px solid var(--gray-100)' : 'none',
                alignItems: 'center', fontSize: 13,
              }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>
                    {item.category || 'Document'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 1 }}>
                    {item.used_in_retraining_count || 0}× used in training
                  </div>
                </div>
                <Badge variant={sourceColor(item.source)}>
                  {item.source === 'public_dataset' ? 'Public' : 'User'}
                </Badge>
                <Badge variant={typeColor(item.data_type)}>
                  {item.data_type || 'unknown'}
                </Badge>
                <div style={{
                  fontWeight: 600,
                  color: (item.quality_score || 0) >= 70 ? 'var(--success)' : 'var(--warning)',
                }}>
                  {item.quality_score || 0}/100
                </div>
                <div style={{ fontSize: 11, color: 'var(--gray-400)' }}>
                  {fmtDate(item.added_to_training_at)}
                </div>
                <button
                  onClick={() => handleDelete(item.id)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}
                >
                  <Trash2 size={14} color="var(--danger)" />
                </button>
              </div>
            ))}
          </Card>

          {/* Pagination */}
          {(meta.total || 0) > LIMIT && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: 10, marginTop: 14 }}>
              <Button
                variant="secondary" size="sm"
                disabled={skip === 0}
                onClick={() => setSkip((p) => Math.max(0, p - LIMIT))}
              >
                Previous
              </Button>
              <span style={{ fontSize: 13, color: 'var(--gray-500)', padding: '6px 0' }}>
                {skip + 1}–{Math.min(skip + LIMIT, meta.total)} of {meta.total}
              </span>
              <Button
                variant="secondary" size="sm"
                disabled={skip + LIMIT >= (meta.total || 0)}
                onClick={() => setSkip((p) => p + LIMIT)}
              >
                Next
              </Button>
            </div>
          )}
        </div>

        {/* Validation rules panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 4, fontSize: 15 }}>Validation Rules</h3>
            <p style={{ fontSize: 12, color: 'var(--gray-500)', marginBottom: 16, lineHeight: 1.5 }}>
              Adjust auto-approve and auto-reject score thresholds.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--success)' }}>
                    Auto-Approve ≥
                  </label>
                  <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--success)' }}>
                    {approveThreshold}
                  </span>
                </div>
                <input
                  type="range" min={50} max={90} value={approveThreshold}
                  onChange={(e) => setApproveThreshold(Number(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--success)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--gray-400)' }}>
                  <span>50</span><span>90</span>
                </div>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--danger)' }}>
                    Auto-Reject &lt;
                  </label>
                  <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--danger)' }}>
                    {rejectThreshold}
                  </span>
                </div>
                <input
                  type="range" min={10} max={60} value={rejectThreshold}
                  onChange={(e) => setRejectThreshold(Number(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--danger)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--gray-400)' }}>
                  <span>10</span><span>60</span>
                </div>
              </div>

              {/* Visual legend */}
              <div style={{ fontSize: 12, lineHeight: 1.8 }}>
                <div style={{ color: 'var(--danger)' }}>
                  ✗ 0–{rejectThreshold - 1} → Auto-rejected
                </div>
                <div style={{ color: 'var(--warning)' }}>
                  ⟳ {rejectThreshold}–{approveThreshold - 1} → Admin review
                </div>
                <div style={{ color: 'var(--success)' }}>
                  ✓ {approveThreshold}–100 → Auto-approved
                </div>
              </div>

              <Button onClick={handleSaveRules} loading={savingRules} fullWidth>
                Save Rules
              </Button>
            </div>
          </Card>

          {/* Data distribution */}
          {meta.total > 0 && (
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 12, fontSize: 14 }}>Data Mix</h3>
              {[
                { label: 'Public Datasets', value: meta.public_dataset_count || 0, total: meta.total, color: 'var(--info)'    },
                { label: 'User Uploads',    value: meta.user_upload_count    || 0, total: meta.total, color: 'var(--purple)'  },
                { label: 'Resumes',         value: meta.resume_count         || 0, total: meta.total, color: 'var(--success)' },
                { label: 'Job Descriptions',value: meta.job_description_count|| 0, total: meta.total, color: 'var(--warning)' },
              ].map((s) => (
                <div key={s.label} style={{ marginBottom: 10 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 3, fontSize: 12 }}>
                    <span style={{ color: 'var(--gray-600)' }}>{s.label}</span>
                    <span style={{ fontWeight: 600 }}>{s.value}</span>
                  </div>
                  <div style={{ height: 5, background: 'var(--gray-100)', borderRadius: 999 }}>
                    <div style={{
                      height: '100%',
                      width: `${s.total > 0 ? (s.value / s.total) * 100 : 0}%`,
                      background: s.color,
                      borderRadius: 999,
                    }} />
                  </div>
                </div>
              ))}
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}