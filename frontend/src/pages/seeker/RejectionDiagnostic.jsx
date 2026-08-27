import { useState, useEffect } from 'react'
import { sharedAPI } from '../../api/shared'
import { seekerAPI } from '../../api/seeker'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Badge from '../../components/ui/Badge'
import ScoreBar from '../../components/ui/ScoreBar'
import { AlertCircle, ArrowUp } from 'lucide-react'

export default function RejectionDiagnostic() {
  const [resumes, setResumes]   = useState([])
  const [resumeId, setResumeId] = useState('')
  const [jdText, setJdText]     = useState('')
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)

  useEffect(() => {
    sharedAPI.getMyResumes().then((r) => {
      const list = r.data.resumes || []
      setResumes(list)
      if (list.length > 0) setResumeId(list[0].id)
    })
  }, [])

  const handleDiagnose = async () => {
    if (!resumeId || !jdText.trim()) {
      toast.error('Select a resume and paste a job description')
      return
    }
    setLoading(true)
    try {
      const res = await seekerAPI.rejectionDiagnostic({ resume_id: resumeId, jd_text: jdText })
      setResult(res.data)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Diagnosis failed')
    } finally {
      setLoading(false)
    }
  }

  const impactColor = (impact) =>
    impact === 'High' ? 'var(--danger)' : impact === 'Medium' ? 'var(--warning)' : 'var(--info)'

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Rejection Diagnostic</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Understand exactly why your resume was rejected and how to fix it
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: result ? '1fr 1fr' : '600px', gap: 24 }}>
        {/* Inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Select Resume</h3>
            {resumes.length === 0 ? (
              <p style={{ color: 'var(--gray-400)', fontSize: 13 }}>Upload a resume first via Resume Enhancer.</p>
            ) : (
              <select
                value={resumeId}
                onChange={(e) => setResumeId(e.target.value)}
                style={{
                  width: '100%', padding: '9px 12px',
                  border: '1px solid var(--gray-300)',
                  borderRadius: 'var(--radius)', fontSize: 14,
                  background: '#fff',
                }}
              >
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>{r.original_filename}</option>
                ))}
              </select>
            )}
          </Card>

          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Job Description</h3>
            <Input
              name="jd" rows={10}
              placeholder="Paste the job description you applied to..."
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
            />
          </Card>

          <Button onClick={handleDiagnose} loading={loading} fullWidth size="lg" variant="danger">
            <AlertCircle size={16} /> Diagnose Rejection
          </Button>
        </div>

        {/* Results */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

            {/* Primary reason */}
            <Card style={{ background: '#fef2f2', border: '1px solid #fecaca' }}>
              <div style={{ display: 'flex', gap: 12 }}>
                <AlertCircle size={20} color="var(--danger)" style={{ flexShrink: 0, marginTop: 2 }} />
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--danger)', marginBottom: 4 }}>
                    Primary Rejection Reason
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--gray-700)', lineHeight: 1.6 }}>
                    {result.primary_rejection_reason}
                  </p>
                </div>
              </div>
            </Card>

            {/* Score */}
            <Card>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                <span style={{ fontWeight: 600 }}>Match Score</span>
                <span style={{ fontSize: 22, fontWeight: 700, color: 'var(--danger)' }}>
                  {Math.round(result.overall_score)}%
                </span>
              </div>
              <ScoreBar score={result.overall_score} />
              <p style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 8 }}>
                {result.improvement_potential}
              </p>
            </Card>

            {/* Missing skills */}
            {result.missing_skills?.length > 0 && (
              <Card>
                <h3 style={{ fontWeight: 600, marginBottom: 10, color: 'var(--danger)' }}>
                  Missing Skills ({result.missing_skills.length})
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {result.missing_skills.map((s) => (
                    <Badge key={s} variant="danger">{s}</Badge>
                  ))}
                </div>
              </Card>
            )}

            {/* Weak sections */}
            {result.weak_sections?.length > 0 && (
              <Card>
                <h3 style={{ fontWeight: 600, marginBottom: 10, color: 'var(--warning)' }}>
                  Weak / Missing Sections
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {result.weak_sections.map((s) => (
                    <Badge key={s} variant="warning">{s}</Badge>
                  ))}
                </div>
              </Card>
            )}

            {/* Priority suggestions */}
            {result.priority_suggestions?.length > 0 && (
              <Card>
                <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Priority Actions</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {result.priority_suggestions.map((s, i) => (
                    <div key={i} style={{
                      padding: '12px 14px',
                      borderRadius: 8,
                      border: '1px solid var(--gray-200)',
                      background: 'var(--gray-50)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                        <span style={{ fontWeight: 600, fontSize: 13 }}>
                          #{s.priority} {s.action}
                        </span>
                        <span style={{
                          fontSize: 11, fontWeight: 600, padding: '2px 8px',
                          borderRadius: 999, background: '#fee2e2',
                          color: impactColor(s.impact),
                        }}>
                          {s.impact} Impact
                        </span>
                      </div>
                      <p style={{ fontSize: 12, color: 'var(--gray-600)', lineHeight: 1.5 }}>
                        {s.detail}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            )}

            {/* Formatting issues */}
            {result.formatting_issues?.length > 0 && (
              <Card>
                <h3 style={{ fontWeight: 600, marginBottom: 10 }}>Formatting Issues</h3>
                {result.formatting_issues.map((f, i) => (
                  <p key={i} style={{ fontSize: 13, color: 'var(--warning)', marginBottom: 4 }}>⚠ {f}</p>
                ))}
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  )
}