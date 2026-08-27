import { useState, useEffect } from 'react'
import { sharedAPI } from '../../api/shared'
import { seekerAPI } from '../../api/seeker'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import ScoreBar from '../../components/ui/ScoreBar'
import FileDropzone from '../../components/ui/FileDropzone'
import Badge from '../../components/ui/Badge'
import { CheckCircle, XCircle, Upload, Zap, BookOpen, User, ShieldAlert, Award, Star, ArrowRight } from 'lucide-react'

export default function ResumeEnhancer() {
  const [resumes, setResumes]     = useState([])
  const [resumeId, setResumeId]   = useState('')
  const [jobs, setJobs]           = useState([])
  const [jobId, setJobId]         = useState('')
  const [jdText, setJdText]       = useState('')
  const [inputType, setInputType] = useState('select') // 'select' | 'paste'
  const [file, setFile]           = useState(null)
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading]     = useState(false)
  const [result, setResult]       = useState(null)

  useEffect(() => {
    sharedAPI.getMyResumes().then((r) => {
      setResumes(r.data.resumes || [])
      if (r.data.resumes?.length > 0) setResumeId(r.data.resumes[0].id)
    })
    seekerAPI.getJobs().then((r) => {
      setJobs(r.data.jobs || [])
      if (r.data.jobs?.length > 0) setJobId(r.data.jobs[0]._id || r.data.jobs[0].id)
    })
  }, [])

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', file)
      const res = await sharedAPI.uploadResume(fd)
      toast.success('Resume uploaded!')
      const newResume = res.data.resume
      setResumes((p) => [newResume, ...p])
      setResumeId(newResume.id)
      setFile(null)
    } catch {
      toast.error('Upload failed')
    } finally {
      setUploading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!resumeId) {
      toast.error('Select a resume first')
      return
    }
    if (inputType === 'select' && !jobId) {
      toast.error('Select a target job post')
      return
    }
    if (inputType === 'paste' && !jdText.trim()) {
      toast.error('Paste a job description')
      return
    }

    setLoading(true)
    try {
      const payload = { resume_id: resumeId }
      if (inputType === 'select') {
        payload.job_id = jobId
      } else {
        payload.jd_text = jdText
      }
      const res = await seekerAPI.resumeEnhancer(payload)
      setResult(res.data)
      toast.success('Resume compatibility analysis completed!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  const scoreColor = (s) => s >= 85 ? 'var(--success)' : s >= 70 ? 'var(--primary)' : s >= 55 ? 'var(--warning)' : 'var(--danger)'

  const getPriorityBadgeVariant = (priority) => {
    if (priority === 'High') return 'danger'
    if (priority === 'Medium') return 'warning'
    return 'gray'
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Resume Match Enhancer</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Optimize your resume to fit target recruiter job profiles or arbitrary job description texts
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: result ? '400px 1fr' : '1fr', gap: 24, alignItems: 'start' }}>
        {/* Left Column — Input Settings */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          
          {/* Upload Resume */}
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Upload Resume</h3>
            <FileDropzone
              onDrop={(f) => setFile(f[0])}
              file={file}
              hint="PDF or DOCX · max 5MB"
            />
            {file && (
              <Button onClick={handleUpload} loading={uploading} style={{ marginTop: 12 }} fullWidth>
                <Upload size={15} /> Upload
              </Button>
            )}
          </Card>

          {/* Select Resume */}
          {resumes.length > 0 && (
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Select Resume</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {resumes.map((r) => (
                  <label key={r.id} style={{
                    display: 'flex', alignItems: 'center', gap: 10,
                    padding: '10px 14px', borderRadius: 8, cursor: 'pointer',
                    border: `2px solid ${resumeId === r.id ? 'var(--primary)' : 'var(--gray-200)'}`,
                    background: resumeId === r.id ? 'var(--primary-light)' : 'var(--card-bg, #fff)',
                    transition: 'all 0.12s',
                  }}>
                    <input
                      type="radio" name="resume" value={r.id}
                      checked={resumeId === r.id}
                      onChange={() => setResumeId(r.id)}
                      style={{ accentColor: 'var(--primary)' }}
                    />
                    <div style={{ overflow: 'hidden' }}>
                      <div style={{ fontSize: 13, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {r.original_filename}
                      </div>
                      <div style={{ fontSize: 11, color: 'var(--gray-400)' }}>
                        {r.char_count?.toLocaleString()} chars · Uploaded {new Date(r.uploaded_at).toLocaleDateString()}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </Card>
          )}

          {/* Target Job Selector */}
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Target Job Requirement</h3>
            
            <div style={{ display: 'flex', border: '1px solid var(--gray-200)', borderRadius: 8, overflow: 'hidden', marginBottom: 16 }}>
              <button
                style={{
                  flex: 1, padding: '8px 12px', fontSize: 12, fontWeight: 600, border: 'none', cursor: 'pointer',
                  background: inputType === 'select' ? 'var(--primary-light)' : 'var(--card-bg, #fff)',
                  color: inputType === 'select' ? 'var(--primary-dark)' : 'var(--gray-600)'
                }}
                onClick={() => setInputType('select')}
              >
                Select Job Post
              </button>
              <button
                style={{
                  flex: 1, padding: '8px 12px', fontSize: 12, fontWeight: 600, border: 'none', cursor: 'pointer',
                  background: inputType === 'paste' ? 'var(--primary-light)' : 'var(--card-bg, #fff)',
                  color: inputType === 'paste' ? 'var(--primary-dark)' : 'var(--gray-600)'
                }}
                onClick={() => setInputType('paste')}
              >
                Paste JD Text
              </button>
            </div>

            {inputType === 'select' ? (
              <div>
                <select
                  value={jobId}
                  onChange={(e) => setJobId(e.target.value)}
                  style={{
                    width: '100%', padding: '9px 12px', border: '1px solid var(--gray-300)',
                    borderRadius: 8, fontSize: 13, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)', cursor: 'pointer'
                  }}
                >
                  {jobs.map((j) => (
                    <option key={j._id || j.id} value={j._id || j.id}>
                      {j.title} ({j.company_name})
                    </option>
                  ))}
                  {jobs.length === 0 && (
                    <option value="">No open job posts available</option>
                  )}
                </select>
              </div>
            ) : (
              <textarea
                placeholder="Paste the target job description text here..."
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                rows={6}
                style={{
                  width: '100%', padding: '9px 12px', border: '1px solid var(--gray-300)',
                  borderRadius: 8, fontSize: 13, resize: 'vertical', lineHeight: 1.5, fontFamily: 'inherit'
                }}
              />
            )}
          </Card>

          <Button onClick={handleAnalyze} loading={loading} fullWidth size="lg">
            <Zap size={16} /> Analyze & Enhance Resume
          </Button>
        </div>

        {/* Right Column — Professional Dashboard Results */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            
            {/* Match & Eligibility Banner */}
            <Card>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <div>
                  <div style={{ fontSize: 64, fontWeight: 800, color: scoreColor(result.overall_score), lineHeight: 1 }}>
                    {Math.round(result.overall_score)}
                    <span style={{ fontSize: 24, color: 'var(--gray-400)' }}>%</span>
                  </div>
                  <div style={{ marginTop: 8 }}>
                    <Badge variant={result.interview_eligible ? 'success' : 'danger'} style={{ fontSize: 13, padding: '4px 16px' }}>
                      {result.eligibility_label}
                    </Badge>
                  </div>
                </div>

                <div style={{ textAlign: 'right', maxWidth: 300 }}>
                  <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--gray-800)' }}>
                    ATS Check Score: <span style={{ color: scoreColor(result.ats_score) }}>{result.ats_score}/100</span>
                  </p>
                  <p style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 4, lineHeight: 1.5 }}>
                    {result.selection_probability}
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 18 }}>
                <ScoreBar score={result.embedding_score} label="Semantic Language Match" />
                <ScoreBar score={result.skill_overlap_score} label="Required Skills Coverage" />
              </div>
            </Card>

            {/* Experience & Education Comparison */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <Card>
                <h4 style={{ fontWeight: 600, fontSize: 13, color: 'var(--gray-500)', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
                  <User size={15} /> Experience Metrics
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span style={{ color: 'var(--gray-600)' }}>Required Experience:</span>
                    <span style={{ fontWeight: 600 }}>{result.experience.required !== null ? `${result.experience.required} Years` : 'Not Specified'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span style={{ color: 'var(--gray-600)' }}>Detected Experience:</span>
                    <span style={{ fontWeight: 600 }}>{result.experience.candidate !== null ? `${result.experience.candidate} Years` : '0 Years'}</span>
                  </div>
                  <div style={{ borderTop: '1px solid var(--gray-100)', marginTop: 6, paddingTop: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 12, color: 'var(--gray-500)' }}>Requirement Status:</span>
                    <Badge variant={result.experience.status === 'meets_requirement' ? 'success' : 'warning'}>
                      {result.experience.status === 'meets_requirement' ? 'Meets Requirement' : 'Below Requirement'}
                    </Badge>
                  </div>
                </div>
              </Card>

              <Card>
                <h4 style={{ fontWeight: 600, fontSize: 13, color: 'var(--gray-500)', display: 'flex', alignItems: 'center', gap: 6, marginBottom: 12 }}>
                  <Award size={15} /> Education Qualifications
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span style={{ color: 'var(--gray-600)' }}>Required Degree:</span>
                    <span style={{ fontWeight: 600 }}>{result.education.required || 'Not Specified'}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span style={{ color: 'var(--gray-600)' }}>Detected Degree:</span>
                    <span style={{ fontWeight: 600 }}>{result.education.candidate || 'None Detected'}</span>
                  </div>
                  <div style={{ borderTop: '1px solid var(--gray-100)', marginTop: 6, paddingTop: 6, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: 12, color: 'var(--gray-500)' }}>Requirement Status:</span>
                    <Badge variant={result.education.match === true || result.education.match === 'unknown' ? 'success' : 'danger'}>
                      {result.education.match === true || result.education.match === 'unknown' ? 'Meets/Exceeds' : 'Unmet'}
                    </Badge>
                  </div>
                </div>
              </Card>
            </div>

            {/* Required Skills Splits */}
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 14, fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                <BookOpen size={16} color="var(--primary)" /> Skills Analysis & Overlap
              </h3>

              {/* Required Skills */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--success)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <CheckCircle size={13} /> Matched Required Skills ({result.matched_required_skills.length})
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {result.matched_required_skills.map((s) => (
                      <Badge key={s} variant="success">{s}</Badge>
                    ))}
                    {result.matched_required_skills.length === 0 && (
                      <span style={{ fontSize: 12, color: 'var(--gray-400)' }}>None</span>
                    )}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--danger)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <XCircle size={13} /> Missing Required Skills ({result.missing_required_skills.length})
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {result.missing_required_skills.map((s) => (
                      <Badge key={s} variant="danger">{s}</Badge>
                    ))}
                    {result.missing_required_skills.length === 0 && (
                      <span style={{ fontSize: 12, color: 'var(--success)' }}>No required skills missing!</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Preferred Skills */}
              {(result.matched_preferred_skills.length > 0 || result.missing_preferred_skills.length > 0) && (
                <div style={{ marginTop: 14, borderTop: '1px solid var(--gray-200)', paddingTop: 14 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {result.matched_preferred_skills.length > 0 && (
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--primary)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                          <Star size={13} color="var(--primary)" /> Matched Preferred Skills ({result.matched_preferred_skills.length})
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                          {result.matched_preferred_skills.map((s) => (
                            <Badge key={s} variant="purple">{s}</Badge>
                          ))}
                        </div>
                      </div>
                    )}

                    {result.missing_preferred_skills.length > 0 && (
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--gray-500)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                          <Star size={13} color="var(--gray-400)" /> Missing Preferred Skills ({result.missing_preferred_skills.length})
                        </div>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                          {result.missing_preferred_skills.map((s) => (
                            <Badge key={s} variant="gray">{s}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </Card>

            {/* Keyword gaps */}
            {result.important_missing_keywords.length > 0 && (
              <Card>
                <h3 style={{ fontWeight: 600, marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <ShieldAlert size={16} color="var(--warning)" /> Critical Keyword Gaps
                </h3>
                <p style={{ fontSize: 12, color: 'var(--gray-500)', marginBottom: 8 }}>
                  These terms are highly weighted in the job requirements but are absent from your resume:
                </p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {result.important_missing_keywords.map((k) => (
                    <Badge key={k} variant="danger" style={{ fontSize: 10 }}>{k}</Badge>
                  ))}
                </div>
              </Card>
            )}

            {/* Section presence */}
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 14, fontSize: 14 }}>Section Coverage</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                <div>
                  <div style={{ fontSize: 12, color: 'var(--success)', fontWeight: 600, marginBottom: 6 }}>
                    Detected Resume Headings:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {result.detected_sections.map((s) => (
                      <Badge key={s} variant="success">{s}</Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 12, color: 'var(--danger)', fontWeight: 600, marginBottom: 6 }}>
                    Missing Recommended Headings:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {result.missing_recommended_sections.map((s) => (
                      <Badge key={s} variant="danger">{s}</Badge>
                    ))}
                    {result.missing_recommended_sections.length === 0 && (
                      <span style={{ fontSize: 12, color: 'var(--success)' }}>All sections present!</span>
                    )}
                  </div>
                </div>
              </div>
            </Card>

            {/* Strengths & Weaknesses */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <Card>
                <h3 style={{ fontWeight: 600, color: 'var(--success)', marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 5 }}>
                  <CheckCircle size={15} /> Resume Strengths
                </h3>
                <ul style={{ paddingLeft: 18, margin: 0, fontSize: 13, lineHeight: 1.6, color: 'var(--gray-700)' }}>
                  {result.resume_strengths.map((s, idx) => (
                    <li key={idx} style={{ marginBottom: 4 }}>{s}</li>
                  ))}
                </ul>
              </Card>

              <Card>
                <h3 style={{ fontWeight: 600, color: 'var(--warning)', marginBottom: 12, fontSize: 14, display: 'flex', alignItems: 'center', gap: 5 }}>
                  <ShieldAlert size={15} /> Formatting Warnings
                </h3>
                <ul style={{ paddingLeft: 18, margin: 0, fontSize: 13, lineHeight: 1.6, color: 'var(--gray-700)' }}>
                  {result.ats_weaknesses.map((w, idx) => (
                    <li key={idx} style={{ marginBottom: 4 }}>{w}</li>
                  ))}
                  {result.ats_weaknesses.length === 0 && (
                    <li style={{ color: 'var(--success)', fontWeight: 500 }}>No formatting issues detected!</li>
                  )}
                </ul>
              </Card>
            </div>

            {/* Prioritized recommendations */}
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                <ArrowRight size={18} color="var(--primary)" /> Prioritized Actionable Recommendations
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {result.prioritized_actionable_improvements.map((rec, i) => (
                  <div key={i} style={{
                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                    padding: '12px 16px', background: 'var(--gray-50)',
                    borderLeft: `4px solid ${rec.priority === 'High' ? 'var(--danger)' : rec.priority === 'Medium' ? 'var(--warning)' : 'var(--primary)'}`,
                    borderRadius: '0 8px 8px 0', fontSize: 13, lineHeight: 1.5
                  }}>
                    <span style={{ color: 'var(--gray-800)' }}>{rec.text}</span>
                    <Badge variant={getPriorityBadgeVariant(rec.priority)}>
                      {rec.priority} Priority
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>

          </div>
        )}
      </div>
    </div>
  )
}