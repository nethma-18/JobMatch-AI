import { useState, useEffect } from 'react'
import { hrAPI } from '../../api/hr'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import ScoreBar from '../../components/ui/ScoreBar'
import { TrendingUp, Shield, CheckCircle, XCircle, Briefcase, GraduationCap, Info } from 'lucide-react'

export default function SkillGap() {
  const [jobs, setJobs]         = useState([])
  const [jobId, setJobId]       = useState('')
  const [rankings, setRankings] = useState([])
  const [resumeId, setResumeId] = useState('')
  const [blindMode, setBlindMode] = useState(false)
  const [loading, setLoading]   = useState(false)
  const [result, setResult]     = useState(null)

  useEffect(() => {
    hrAPI.getJobs({ status: 'open' }).then((r) => {
      const list = r.data.jobs || []
      setJobs(list)
      if (list.length > 0) setJobId(list[0].id)
    })
  }, [])

  useEffect(() => {
    if (!jobId) return
    hrAPI.getRankings(jobId)
      .then((r) => {
        const list = r.data?.rankings || []
        setRankings(list)
        if (list.length > 0) setResumeId(list[0].resume_id)
      })
      .catch(() => setRankings([]))
  }, [jobId])

  const handleAnalyze = async () => {
    if (!resumeId || !jobId) { toast.error('Select a job and candidate'); return }
    setLoading(true)
    try {
      const res = await hrAPI.skillGap({ resume_id: resumeId, job_id: jobId, blind_mode: blindMode })
      setResult(res.data)
      toast.success('Skill gap analysis complete!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const severityColor = (s) => {
    if (s === 'None') return 'var(--success)'
    if (s === 'Low') return 'var(--success)'
    if (s === 'Medium') return 'var(--warning)'
    if (s === 'High') return 'var(--danger)'
    if (s === 'Critical') return 'var(--danger)'
    return 'var(--gray-500)'
  }

  const selectStyle = {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--gray-300)',
    borderRadius: 10, fontSize: 14, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)',
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Skill Gap Analysis</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Compare candidate skills against job requirements
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 24 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Settings</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 6 }}>
                  Job Post
                </label>
                <select value={jobId} onChange={(e) => setJobId(e.target.value)} style={selectStyle}>
                  {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 6 }}>
                  Candidate
                </label>
                <select value={resumeId} onChange={(e) => setResumeId(e.target.value)} style={selectStyle}>
                  <option value="">-- Select candidate --</option>
                  {rankings.map((r) => (
                    <option key={r.resume_id} value={r.resume_id}>
                      {r.candidate_name || r.filename} — {Math.round(r.score)}%
                    </option>
                  ))}
                </select>
              </div>

              {/* Blind screening toggle */}
              <div style={{
                borderTop: '1px solid var(--gray-200)',
                paddingTop: 12,
                display: 'flex',
                alignItems: 'center',
                justify: 'space-between',
              }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 5 }}>
                    <Shield size={14} color="var(--primary)" /> Blind Screening
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--gray-500)', marginTop: 2 }}>
                    Hide candidate identity in analysis
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={blindMode}
                  onChange={(e) => setBlindMode(e.target.checked)}
                  style={{ width: 18, height: 18, cursor: 'pointer', accentColor: 'var(--primary)' }}
                />
              </div>
            </div>
          </Card>
          <Button onClick={handleAnalyze} loading={loading} fullWidth size="lg">
            <TrendingUp size={16} /> Analyze Skill Gap
          </Button>
        </div>

        <div>
          {result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Summary Card */}
              <Card>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                  <div>
                    <h3 style={{ fontWeight: 700, fontSize: 18, display: 'flex', alignItems: 'center', gap: 6 }}>
                      {result.candidate_name}
                      {blindMode && (
                        <Badge variant="warning" style={{ fontSize: 10, display: 'flex', alignItems: 'center', gap: 3 }}>
                          <Shield size={10} /> Blind Profile
                        </Badge>
                      )}
                    </h3>
                    <p style={{ fontSize: 13, color: 'var(--gray-500)', marginTop: 2 }}>{result.recommendation}</p>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 28, fontWeight: 800, color: severityColor(result.gap_severity) }}>
                      {result.match_percentage}%
                    </div>
                    <Badge variant={
                      result.gap_severity === 'Low' || result.gap_severity === 'None' ? 'success' :
                      result.gap_severity === 'Medium' ? 'warning' : 'danger'
                    }>
                      {result.gap_severity} Gap
                    </Badge>
                  </div>
                </div>
                <ScoreBar score={result.match_percentage} />
                <div style={{ display: 'flex', gap: 20, marginTop: 14 }}>
                  {[
                    { label: 'Required Skills', value: result.total_required, color: 'var(--gray-600)' },
                    { label: 'Matched',  value: result.total_matched,  color: 'var(--success)'  },
                    { label: 'Missing',  value: result.total_missing,   color: 'var(--danger)'   },
                  ].map((s) => (
                    <div key={s.label} style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</div>
                      <div style={{ fontSize: 12, color: 'var(--gray-400)' }}>{s.label}</div>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Skills Analysis Split Panel */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {/* Required Skills Card */}
                <Card>
                  <h3 style={{ fontWeight: 600, color: 'var(--success)', marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 5 }}>
                    <CheckCircle size={15} /> Required Skills Matched
                  </h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {(result.required_skills?.matched || result.matched_skills || []).map((s) => (
                      <Badge key={s} variant="success">{s}</Badge>
                    ))}
                    {(result.required_skills?.matched || result.matched_skills || []).length === 0 && (
                      <p style={{ fontSize: 13, color: 'var(--gray-400)' }}>No matches</p>
                    )}
                  </div>
                </Card>

                {/* Missing Required Skills Card */}
                <Card>
                  <h3 style={{ fontWeight: 600, color: 'var(--danger)', marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 5 }}>
                    <XCircle size={15} /> Required Skills Missing
                  </h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {(result.required_skills?.missing || result.missing_skills || []).map((s) => (
                      <Badge key={s} variant="danger">{s}</Badge>
                    ))}
                    {(result.required_skills?.missing || result.missing_skills || []).length === 0 && (
                      <p style={{ fontSize: 13, color: 'var(--success)' }}>No gaps — perfect match!</p>
                    )}
                  </div>
                </Card>
              </div>

              {/* Preferred Skills Panel */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {/* Preferred Skills Matched */}
                <Card>
                  <h3 style={{ fontWeight: 600, color: 'var(--success)', marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 5 }}>
                    <CheckCircle size={15} /> Preferred Skills Matched
                  </h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {(result.preferred_skills?.matched || []).map((s) => (
                      <Badge key={s} variant="success">{s}</Badge>
                    ))}
                    {(result.preferred_skills?.matched || []).length === 0 && (
                      <p style={{ fontSize: 13, color: 'var(--gray-400)' }}>None matched</p>
                    )}
                  </div>
                </Card>

                {/* Preferred Skills Missing */}
                <Card>
                  <h3 style={{ fontWeight: 600, color: 'var(--gray-500)', marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 5 }}>
                    <XCircle size={15} /> Preferred Skills Missing
                  </h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {(result.preferred_skills?.missing || []).map((s) => (
                      <Badge key={s} variant="gray">{s}</Badge>
                    ))}
                    {(result.preferred_skills?.missing || []).length === 0 && (
                      <p style={{ fontSize: 13, color: 'var(--success)' }}>None missing</p>
                    )}
                  </div>
                </Card>
              </div>

              {/* Extra Candidate Skills */}
              {(result.extra_skills?.length > 0 || result.additional_skills?.length > 0) && (
                <Card>
                  <h3 style={{ fontWeight: 600, marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 5 }}>
                    <Info size={15} color="var(--primary)" /> Extra Candidate Skills (Additional assets)
                  </h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {(result.extra_skills || result.additional_skills || []).map((s) => (
                      <Badge key={s} variant="purple">{s}</Badge>
                    ))}
                  </div>
                </Card>
              )}

              {/* Experience and Education Comparison */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {/* Experience Gap Card */}
                <Card>
                  <h3 style={{ fontWeight: 600, marginBottom: 14, fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <Briefcase size={15} color="var(--primary)" /> Experience Comparison
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                      <span style={{ color: 'var(--gray-500)' }}>Required:</span>
                      <span style={{ fontWeight: 600 }}>
                        {result.experience?.required !== null && result.experience?.required !== undefined
                          ? `${result.experience.required} year(s)`
                          : 'No required minimum'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                      <span style={{ color: 'var(--gray-500)' }}>Candidate:</span>
                      <span style={{ fontWeight: 600 }}>
                        {result.experience?.candidate !== null && result.experience?.candidate !== undefined
                          ? `${result.experience.candidate} year(s)`
                          : 'Unknown / Not specified'}
                      </span>
                    </div>
                    {result.experience?.gap !== null && result.experience?.gap !== undefined && (
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                        <span style={{ color: 'var(--gray-500)' }}>Gap:</span>
                        <span style={{ fontWeight: 600, color: result.experience.gap > 0 ? 'var(--danger)' : 'var(--success)' }}>
                          {result.experience.gap > 0 ? `${result.experience.gap} year(s)` : 'None'}
                        </span>
                      </div>
                    )}
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, borderTop: '1px solid var(--gray-100)', paddingTop: 8 }}>
                      <span style={{ color: 'var(--gray-500)' }}>Status:</span>
                      <Badge variant={
                        result.experience?.status === 'meets_requirement' ? 'success' :
                        result.experience?.status === 'below_requirement' ? 'danger' : 'gray'
                      }>
                        {result.experience?.status === 'meets_requirement' ? 'Meets Requirement' :
                         result.experience?.status === 'below_requirement' ? 'Below Requirement' : 'Unknown'}
                      </Badge>
                    </div>
                  </div>
                </Card>

                {/* Education Gap Card */}
                <Card>
                  <h3 style={{ fontWeight: 600, marginBottom: 14, fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <GraduationCap size={15} color="var(--primary)" /> Education Comparison
                  </h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                      <span style={{ color: 'var(--gray-500)' }}>Required Degree:</span>
                      <span style={{ fontWeight: 600 }}>{result.education?.required || 'No degree required'}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                      <span style={{ color: 'var(--gray-500)' }}>Candidate Degree:</span>
                      <span style={{ fontWeight: 600 }}>{result.education?.candidate || 'Unknown / Not specified'}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, borderTop: '1px solid var(--gray-100)', paddingTop: 8 }}>
                      <span style={{ color: 'var(--gray-500)' }}>Status:</span>
                      <Badge variant={
                        result.education?.match === true ? 'success' :
                        result.education?.match === false ? 'danger' : 'gray'
                      }>
                        {result.education?.match === true ? 'Degree Matches' :
                         result.education?.match === false ? 'Degree Mismatch' : 'Unknown'}
                      </Badge>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          ) : (
            <Card style={{ minHeight: 360, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12 }}>
              <TrendingUp size={44} color="var(--gray-300)" />
              <p style={{ color: 'var(--gray-400)', fontSize: 14 }}>Select a job and candidate to analyze</p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}