import { useState, useEffect } from 'react'
import { adminAPI } from '../../api/admin'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import Input from '../../components/ui/Input'
import { fmtDate } from '../../utils/helpers'
import {
  CheckCircle, XCircle, Eye,
  AlertTriangle, Clock,
} from 'lucide-react'

export default function ValidationQueue() {
  const [items, setItems]     = useState([])
  const [total, setTotal]     = useState(0)
  const [loading, setLoading] = useState(true)
  const [skip, setSkip]       = useState(0)
  const LIMIT = 15

  const [selected, setSelected]   = useState(null)
  const [detailOpen, setDetail]   = useState(false)
  const [reason, setReason]       = useState('')
  const [actioning, setActioning] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const res = await adminAPI.getPendingReviews({ skip, limit: LIMIT })
      setItems(res.data.items || [])
      setTotal(res.data.total || 0)
    } catch {} finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [skip])

  const openDetail = async (item) => {
    try {
      const res = await adminAPI.getReviewDetail(item.id)
      setSelected(res.data)
      setReason('')
      setDetail(true)
    } catch {
      toast.error('Could not load details')
    }
  }

  const handleApprove = async (id) => {
    setActioning(true)
    try {
      await adminAPI.approve(id, { reason: reason || 'Admin approved' })
      toast.success('Approved and added to training pool')
      setDetail(false)
      load()
    } catch {
      toast.error('Approval failed')
    } finally { setActioning(false) }
  }

  const handleReject = async (id) => {
    if (!reason.trim()) {
      toast.error('Please provide a rejection reason')
      return
    }
    setActioning(true)
    try {
      await adminAPI.reject(id, { reason })
      toast.success('Rejected and user notified')
      setDetail(false)
      load()
    } catch {
      toast.error('Rejection failed')
    } finally { setActioning(false) }
  }

  const scoreColor = (score) =>
    score >= 70 ? 'var(--success)' :
    score >= 40 ? 'var(--warning)' : 'var(--danger)'

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Validation Queue</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          {total} uploads pending manual review (score 40–69)
        </p>
      </div>

      {/* Summary badges */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
        <Card padding="12px 20px" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Clock size={16} color="var(--warning)" />
          <span style={{ fontWeight: 600, fontSize: 14 }}>{total}</span>
          <span style={{ fontSize: 13, color: 'var(--gray-500)' }}>Pending</span>
        </Card>
        <Card padding="12px 20px" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <AlertTriangle size={16} color="var(--warning)" />
          <span style={{ fontSize: 13, color: 'var(--gray-500)' }}>
            Score 40–69 requires human review
          </span>
        </Card>
      </div>

      {/* Queue table */}
      <Card padding="0">
        {/* Header */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '2fr 1fr 80px 100px 120px 80px',
          padding: '10px 20px',
          background: 'var(--gray-50)',
          borderBottom: '1px solid var(--gray-200)',
          fontSize: 12, fontWeight: 600,
          color: 'var(--gray-500)',
        }}>
          <span>Upload</span>
          <span>Type</span>
          <span>Score</span>
          <span>Issues</span>
          <span>Uploaded</span>
          <span>Action</span>
        </div>

        {loading ? (
          <p style={{ padding: 32, textAlign: 'center', color: 'var(--gray-400)' }}>Loading...</p>
        ) : items.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center' }}>
            <CheckCircle size={36} color="var(--success)" style={{ marginBottom: 12 }} />
            <p style={{ color: 'var(--gray-500)', fontWeight: 500 }}>All clear! No uploads pending review.</p>
          </div>
        ) : items.map((item, i) => (
          <div key={item.id} style={{
            display: 'grid',
            gridTemplateColumns: '2fr 1fr 80px 100px 120px 80px',
            padding: '12px 20px',
            borderBottom: i < items.length - 1 ? '1px solid var(--gray-100)' : 'none',
            alignItems: 'center',
            fontSize: 13,
          }}>
            <div>
              <div style={{ fontWeight: 500 }}>
                {item.file_url?.split('/').pop() || 'Uploaded file'}
              </div>
              <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 1 }}>
                User: {item.user_id?.slice(-8) || '—'}
              </div>
            </div>
            <Badge variant="info">{item.upload_type || 'resume'}</Badge>
            <div style={{
              fontWeight: 700, fontSize: 16,
              color: scoreColor(item.quality_score || 0),
            }}>
              {item.quality_score || 0}
            </div>
            <div style={{ fontSize: 11, color: 'var(--gray-500)' }}>
              {item.all_issues?.length || 0} issue{item.all_issues?.length !== 1 ? 's' : ''}
            </div>
            <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>
              {fmtDate(item.uploaded_at)}
            </div>
            <Button size="sm" variant="secondary" onClick={() => openDetail(item)}>
              <Eye size={13} /> Review
            </Button>
          </div>
        ))}
      </Card>

      {/* Pagination */}
      {total > LIMIT && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 10, marginTop: 16 }}>
          <Button
            variant="secondary" size="sm"
            disabled={skip === 0}
            onClick={() => setSkip((p) => Math.max(0, p - LIMIT))}
          >
            Previous
          </Button>
          <span style={{ fontSize: 13, color: 'var(--gray-500)', padding: '6px 0' }}>
            {skip + 1}–{Math.min(skip + LIMIT, total)} of {total}
          </span>
          <Button
            variant="secondary" size="sm"
            disabled={skip + LIMIT >= total}
            onClick={() => setSkip((p) => p + LIMIT)}
          >
            Next
          </Button>
        </div>
      )}

      {/* Detail Modal */}
      <Modal
        open={detailOpen}
        onClose={() => setDetail(false)}
        title="Review Upload"
        width={600}
      >
        {selected && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Info */}
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr',
              gap: 12, padding: '14px', background: 'var(--gray-50)',
              borderRadius: 8, fontSize: 13,
            }}>
              {[
                { label: 'Type',    value: selected.upload_type   },
                { label: 'Score',   value: selected.quality_score },
                { label: 'Status',  value: selected.validation_status },
                { label: 'Chars',   value: selected.extracted_text?.length?.toLocaleString() || '—' },
              ].map((r) => (
                <div key={r.label}>
                  <div style={{ fontSize: 11, color: 'var(--gray-400)', marginBottom: 2 }}>{r.label}</div>
                  <div style={{ fontWeight: 600 }}>{r.value ?? '—'}</div>
                </div>
              ))}
            </div>

            {/* Issues */}
            {selected.all_issues?.length > 0 && (
              <div>
                <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: 'var(--warning)' }}>
                  Issues Found
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                  {selected.all_issues.map((issue, i) => (
                    <div key={i} style={{
                      padding: '8px 12px', background: '#fffbeb',
                      borderLeft: '3px solid var(--warning)',
                      borderRadius: '0 6px 6px 0', fontSize: 12,
                      color: 'var(--gray-700)', lineHeight: 1.5,
                    }}>
                      {issue}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Text preview */}
            {selected.extracted_text && (
              <div>
                <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Text Preview</p>
                <div style={{
                  padding: 12, background: 'var(--gray-50)',
                  borderRadius: 8, maxHeight: 180,
                  overflowY: 'auto', fontSize: 12,
                  color: 'var(--gray-600)', lineHeight: 1.6,
                  fontFamily: 'monospace', whiteSpace: 'pre-wrap',
                  border: '1px solid var(--gray-200)',
                }}>
                  {selected.extracted_text.slice(0, 800)}
                  {selected.extracted_text.length > 800 && '...'}
                </div>
              </div>
            )}

            {/* Reason input */}
            <Input
              label="Decision Reason (required for rejection)"
              placeholder="e.g. Contains spam patterns / Low quality content / Does not appear to be a resume"
              rows={2}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />

            {/* Actions */}
            <div style={{ display: 'flex', gap: 10 }}>
              <Button
                variant="danger" fullWidth
                onClick={() => handleReject(selected.id)}
                loading={actioning}
              >
                <XCircle size={15} /> Reject
              </Button>
              <Button
                fullWidth
                onClick={() => handleApprove(selected.id)}
                loading={actioning}
              >
                <CheckCircle size={15} /> Approve & Add to Pool
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}