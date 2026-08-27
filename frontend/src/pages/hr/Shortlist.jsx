import { useState, useEffect } from 'react'
import { hrAPI } from '../../api/hr'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import { Star, Download, CheckCircle, XCircle, Archive, Shield } from 'lucide-react'
import { downloadCSV } from '../../utils/helpers'

export default function Shortlist() {
  const [jobs, setJobs]         = useState([])
  const [jobId, setJobId]       = useState('')
  const [blindMode, setBlindMode] = useState(false)
  const [rankings, setRankings] = useState([])
  const [shortlist, setShortlist] = useState(null)
  const [loading, setLoading]   = useState(false)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    hrAPI.getJobs({ status: 'open' }).then((r) => {
      const list = r.data.jobs || []
      setJobs(list)
      if (list.length > 0) setJobId(list[0].id)
    })
  }, [])

  useEffect(() => {
    if (!jobId) return
    setLoading(true)
    Promise.all([
      hrAPI.getRankings(jobId, blindMode).catch(() => ({ data: null })),
      hrAPI.getShortlist(jobId).catch(() => ({ data: null })),
    ]).then(([r, s]) => {
      setRankings(r.data?.candidates_ranked || r.data?.rankings || [])
      setShortlist(s.data)
    }).finally(() => setLoading(false))
  }, [jobId, blindMode])

  const handleAction = async (candidateId, action, rating = null) => {
    try {
      await hrAPI.shortlistCandidate(jobId, {
        candidate_id: candidateId,
        action,
        rating,
      })
      toast.success(`Candidate ${action}`)
      const s = await hrAPI.getShortlist(jobId)
      setShortlist(s.data)
    } catch { toast.error('Action failed') }
  }

  const handleExport = async (format) => {
    setExporting(true)
    try {
      const res = await hrAPI.exportShortlist(jobId, format)
      if (format === 'csv') {
        downloadCSV(res.data, `shortlist_${jobId}.csv`)
        toast.success('CSV downloaded')
      } else {
        toast.success('Exported successfully')
      }
    } catch { toast.error('Export failed') }
    finally { setExporting(false) }
  }

  const getStatus = (candidateId) => {
    const found = shortlist?.candidates?.find(
      (c) => c.candidate_id === candidateId
    )
    return found?.status || null
  }

  const selectStyle = {
    padding: '8px 12px', border: '1px solid var(--gray-300)',
    borderRadius: 8, fontSize: 13, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)',
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Candidate Shortlist</h1>
          <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
            Shortlist, reject, or archive ranked candidates
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <label style={{
            display: 'flex', alignItems: 'center', gap: 6,
            fontSize: 13, fontWeight: 600, color: 'var(--gray-700)',
            cursor: 'pointer', background: '#fff', padding: '6px 12px',
            borderRadius: 8, border: '1px solid var(--gray-300)',
          }}>
            <Shield size={14} color="var(--primary)" />
            Blind Screening
            <input
              type="checkbox"
              checked={blindMode}
              onChange={(e) => setBlindMode(e.target.checked)}
              style={{ width: 16, height: 16, cursor: 'pointer', accentColor: 'var(--primary)' }}
            />
          </label>
          <Button variant="secondary" size="sm" onClick={() => handleExport('csv')} loading={exporting}>
            <Download size={13} /> Export CSV
          </Button>
        </div>
      </div>

      {/* Job selector + summary */}
      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 16, marginBottom: 20 }}>
        <select value={jobId} onChange={(e) => setJobId(e.target.value)} style={{ ...selectStyle, width: '100%' }}>
          {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
        </select>
        {shortlist && (
          <div style={{ display: 'flex', gap: 12 }}>
            {[
              { label: 'Shortlisted', value: shortlist.breakdown?.shortlisted || 0, color: 'var(--success)' },
              { label: 'Rejected',    value: shortlist.breakdown?.rejected    || 0, color: 'var(--danger)'  },
              { label: 'Archived',    value: shortlist.breakdown?.archived    || 0, color: 'var(--gray-500)'},
            ].map((s) => (
              <Card key={s.label} padding="12px 20px" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</span>
                <span style={{ fontSize: 13, color: 'var(--gray-500)' }}>{s.label}</span>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* Ranked candidates */}
      {loading ? (
        <p style={{ color: 'var(--gray-400)', textAlign: 'center', padding: 40 }}>Loading...</p>
      ) : rankings.length === 0 ? (
        <Card style={{ textAlign: 'center', padding: 40 }}>
          <Star size={36} color="var(--gray-300)" style={{ marginBottom: 12 }} />
          <p style={{ color: 'var(--gray-400)', fontSize: 13 }}>
            No ranking found for this job. Run Job Ranking first.
          </p>
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {rankings.map((c) => {
            const status = getStatus(c.resume_id)
            return (
              <Card key={c.resume_id} padding="16px">
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  {/* Rank */}
                  <div style={{
                    width: 36, height: 36, borderRadius: '50%',
                    background: 'var(--gray-100)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontWeight: 700, fontSize: 13, color: 'var(--gray-600)',
                    flexShrink: 0,
                  }}>
                    #{c.rank}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
                      {c.candidate_name || c.filename}
                      {(c.is_anonymized || blindMode) && (
                        <Badge variant="warning" style={{ fontSize: 10, display: 'flex', alignItems: 'center', gap: 3 }}>
                          <Shield size={10} /> Blind Profile
                        </Badge>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 3 }}>
                      <span style={{
                        fontSize: 18, fontWeight: 700,
                        color: c.score >= 70 ? 'var(--success)' : c.score >= 45 ? 'var(--warning)' : 'var(--danger)',
                      }}>
                        {Math.round(c.score)}%
                      </span>
                      <Badge variant={c.interview_eligible ? 'success' : 'gray'}>
                        {c.interview_eligible ? 'Eligible' : 'Below threshold'}
                      </Badge>
                      {status && (
                        <Badge variant={status === 'shortlisted' ? 'success' : status === 'rejected' ? 'danger' : 'gray'}>
                          {status}
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Action buttons */}
                  <div style={{ display: 'flex', gap: 8 }}>
                    <Button
                      size="sm"
                      variant={status === 'shortlisted' ? 'primary' : 'secondary'}
                      onClick={() => handleAction(c.resume_id, 'shortlisted')}
                    >
                      <CheckCircle size={13} /> Shortlist
                    </Button>
                    <Button
                      size="sm"
                      variant={status === 'archived' ? 'secondary' : 'ghost'}
                      onClick={() => handleAction(c.resume_id, 'archived')}
                    >
                      <Archive size={13} /> Archive
                    </Button>
                    <Button
                      size="sm"
                      variant={status === 'rejected' ? 'danger' : 'ghost'}
                      onClick={() => handleAction(c.resume_id, 'rejected')}
                    >
                      <XCircle size={13} /> Reject
                    </Button>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      )}
    </div>
  )
}