import { useState, useEffect } from 'react'
import { sharedAPI } from '../../api/shared'
import { seekerAPI } from '../../api/seeker'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import ScoreBar from '../../components/ui/ScoreBar'
import Badge from '../../components/ui/Badge'
import { CheckCircle, AlertTriangle, XCircle, Shield, Info, BookOpen, AlertCircle } from 'lucide-react'

export default function ATSChecker() {
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

  const handleCheck = async () => {
    if (!resumeId) { toast.error('Select a resume first'); return }
    setLoading(true)
    try {
      const res = await seekerAPI.atsChecker({
        resume_id: resumeId,
        jd_text: jdText.trim() || null
      })
      setResult(res.data)
      toast.success('ATS Compatibility check complete!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Check failed')
    } finally {
      setLoading(false)
    }
  }

  const gradeColor = (score) =>
    score >= 90 ? 'var(--success)' :
    score >= 80 ? 'var(--primary)' :
    score >= 70 ? 'var(--info)'    :
    score >= 60 ? 'var(--warning)' : 'var(--danger)'

  const checkIcon = (score, max) => {
    const pct = (score / max) * 100
    if (pct >= 85) return <CheckCircle size={16} color="var(--success)" />
    if (pct >= 60) return <AlertTriangle size={16} color="var(--warning)" />
    return <XCircle size={16} color="var(--danger)" />
  }

  const labelStyle = {
    fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 6
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>ATS Checker & Quality Analyzer</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Analyze formatting, headings, structure, and keyword density for ATS parsing compatibility
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: result ? '380px 1fr' : '480px', gap: 24, alignItems: 'start' }}>
        {/* Controls Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Shield size={18} color="var(--primary)" /> Select Resume
            </h3>
            {resumes.length === 0 ? (
              <p style={{ color: 'var(--gray-400)', fontSize: 13 }}>
                No resumes uploaded yet. Upload one via Resume Enhancer.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {resumes.map((r) => (
                  <label key={r.id} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '10px 14px', borderRadius: 8, cursor: 'pointer',
                    border: `2px solid ${resumeId === r.id ? 'var(--primary)' : 'var(--gray-200)'}`,
                    background: resumeId === r.id ? 'var(--primary-light)' : '#fff',
                    transition: 'all 0.15s'
                  }}>
                    <input
                      type="radio" name="resume" value={r.id}
                      checked={resumeId === r.id}
                      onChange={() => setResumeId(r.id)}
                      style={{ accentColor: 'var(--primary)' }}
                    />
                    <div style={{ fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {r.original_filename}
                    </div>
                  </label>
                ))}
              </div>
            )}

            {/* Optional JD Textarea */}
            <div style={{ marginTop: 18, borderTop: '1px solid var(--gray-200)', paddingTop: 14 }}>
              <label style={labelStyle}>
                Job Description (Optional)
              </label>
              <textarea
                placeholder="Paste the job description here to analyze keyword and skill alignment..."
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                rows={5}
                style={{
                  width: '100%', padding: '9px 12px', border: '1px solid var(--gray-300)',
                  borderRadius: 10, fontSize: 13, outline: 'none', resize: 'vertical',
                  lineHeight: 1.5, fontFamily: 'inherit'
                }}
              />
              <span style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 4, display: 'block' }}>
                Pasting a Job Description enables comparison of matched vs. missing skills.
              </span>
            </div>
          </Card>

          <Button onClick={handleCheck} loading={loading} fullWidth size="lg" disabled={!resumeId}>
            Run ATS Check
          </Button>

          <Card style={{ background: '#fffbeb', border: '1px solid #fde68a' }}>
            <p style={{ fontSize: 12, color: '#92400e', lineHeight: 1.6 }}>
              <strong>75% of resumes</strong> are screened out by ATS filters before reaching recruiters.
              Optimizing your headings and sections ensures your resume is correctly parsed.
            </p>
          </Card>
        </div>

        {/* Results Column */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Score Summary */}
            <Card>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 48, fontWeight: 800, color: gradeColor(result.ats_score), lineHeight: 1 }}>
                    {result.ats_score}
                    <span style={{ fontSize: 22, color: 'var(--gray-400)' }}>/100</span>
                  </div>
                  <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--gray-600)', marginTop: 6 }}>
                    Grade: <span style={{ color: gradeColor(result.ats_score) }}>{result.grade}</span>
                  </p>
                </div>
                <div style={{ textAlign: 'right', maxWidth: 300 }}>
                  <p style={{ fontSize: 13, color: 'var(--gray-500)', lineHeight: 1.5 }}>
                    {result.summary}
                  </p>
                </div>
              </div>
              <ScoreBar score={result.ats_score} />
            </Card>

            {/* Score Breakdown */}
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Score Breakdown</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                {[
                  { name: 'Text Extractability', score: result.breakdown?.text_extractability, max: 20 },
                  { name: 'Structure Compatibility', score: result.breakdown?.structure, max: 20 },
                  { name: 'Required Headings', score: result.breakdown?.sections, max: 20 },
                  { name: 'Keyword Alignment', score: result.breakdown?.keyword_alignment, max: 25 },
                  { name: 'Formatting & Layout', score: result.breakdown?.formatting, max: 15 },
                ].map((val) => (
                  <div key={val.name} style={{
                    padding: '12px 14px', borderRadius: 8, border: '1px solid var(--gray-200)',
                    background: 'var(--gray-50)'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)' }}>{val.name}</span>
                      <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-600)' }}>
                        {val.score}/{val.max}
                      </span>
                    </div>
                    <ScoreBar score={val.score} max={val.max} showValue={false} />
                  </div>
                ))}
              </div>
            </Card>

            {/* Detected Sections & Headings */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <Card>
                <h3 style={{ fontWeight: 600, color: 'var(--success)', marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 5 }}>
                  <CheckCircle size={15} /> Detected Headings
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {result.sections_found?.map((s) => (
                    <Badge key={s} variant="success">{s}</Badge>
                  ))}
                  {result.sections_found?.length === 0 && (
                    <p style={{ fontSize: 13, color: 'var(--gray-400)' }}>No headers matched standard templates.</p>
                  )}
                </div>
              </Card>

              <Card>
                <h3 style={{ fontWeight: 600, color: 'var(--danger)', marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 5 }}>
                  <XCircle size={15} /> Missing Headings
                </h3>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {result.sections_missing?.map((s) => (
                    <Badge key={s} variant="danger">{s}</Badge>
                  ))}
                  {result.sections_missing?.length === 0 && (
                    <p style={{ fontSize: 13, color: 'var(--success)' }}>All core sections present!</p>
                  )}
                </div>
              </Card>
            </div>

            {/* Keyword Analysis (Skills Alignment) */}
            {result.skills?.detected?.length > 0 && (
              <Card>
                <h3 style={{ fontWeight: 600, marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <BookOpen size={15} color="var(--primary)" /> Skill & Keyword Matches
                </h3>

                {jdText ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    <div>
                      <div style={{ fontSize: 12, color: 'var(--success)', fontWeight: 600, marginBottom: 4 }}>
                        Matched Required Keywords:
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {result.skills.matched_required?.map((s) => (
                          <Badge key={s} variant="success" style={{ fontSize: 10 }}>{s}</Badge>
                        ))}
                        {result.skills.matched_required?.length === 0 && (
                          <span style={{ fontSize: 12, color: 'var(--gray-400)' }}>None</span>
                        )}
                      </div>
                    </div>

                    <div>
                      <div style={{ fontSize: 12, color: 'var(--danger)', fontWeight: 600, marginBottom: 4 }}>
                        Missing Required Keywords:
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {result.skills.missing_required?.map((s) => (
                          <Badge key={s} variant="danger" style={{ fontSize: 10 }}>{s}</Badge>
                        ))}
                        {result.skills.missing_required?.length === 0 && (
                          <span style={{ fontSize: 12, color: 'var(--success)' }}>None missing</span>
                        )}
                      </div>
                    </div>

                    {result.skills.matched_preferred?.length > 0 && (
                      <div>
                        <div style={{ fontSize: 12, color: 'var(--primary)', fontWeight: 600, marginBottom: 4 }}>
                          Matched Preferred Keywords:
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                          {result.skills.matched_preferred?.map((s) => (
                            <Badge key={s} variant="purple" style={{ fontSize: 10 }}>{s}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div>
                    <div style={{ fontSize: 12, color: 'var(--gray-500)', marginBottom: 6 }}>
                      Extracted Resume Skills:
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                      {result.skills.detected.map((s) => (
                        <Badge key={s} variant="gray">{s}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            )}

            {/* Strengths & Improvements */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              {/* Strengths */}
              <Card>
                <h3 style={{ fontWeight: 600, color: 'var(--success)', marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 5 }}>
                  <CheckCircle size={15} /> Resume Strengths
                </h3>
                <ul style={{ paddingLeft: 18, margin: 0, fontSize: 13, lineHeight: 1.6, color: 'var(--gray-700)' }}>
                  {result.strengths?.map((s, idx) => (
                    <li key={idx} style={{ marginBottom: 6 }}>{s}</li>
                  ))}
                  {result.strengths?.length === 0 && (
                    <li style={{ color: 'var(--gray-400)' }}>No major strengths detected.</li>
                  )}
                </ul>
              </Card>

              {/* Improvements */}
              <Card>
                <h3 style={{ fontWeight: 600, color: 'var(--warning)', marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 5 }}>
                  <AlertCircle size={15} /> Actionable Fixes
                </h3>
                <ul style={{ paddingLeft: 18, margin: 0, fontSize: 13, lineHeight: 1.6, color: 'var(--gray-700)' }}>
                  {result.improvements?.map((s, idx) => (
                    <li key={idx} style={{ marginBottom: 6 }}>{s}</li>
                  ))}
                  {result.improvements?.length === 0 && (
                    <li style={{ color: 'var(--success)', fontWeight: 500 }}>No issues found — your resume layout is pristine!</li>
                  )}
                </ul>
              </Card>
            </div>

          </div>
        )}
      </div>
    </div>
  )
}