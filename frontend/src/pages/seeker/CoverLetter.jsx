import { useState, useEffect } from 'react'
import { sharedAPI } from '../../api/shared'
import { seekerAPI } from '../../api/seeker'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Badge from '../../components/ui/Badge'
import { Mail, Copy, Download, Star, Shield, HelpCircle, Save } from 'lucide-react'

const TONES = ['professional', 'enthusiastic', 'concise']

export default function CoverLetter() {
  const [resumes, setResumes]       = useState([])
  const [resumeId, setResumeId]     = useState('')
  const [jobs, setJobs]             = useState([])
  const [jobId, setJobId]           = useState('')
  const [jdText, setJdText]         = useState('')
  const [inputType, setInputType] = useState('select') // 'select' | 'paste'
  const [companyName, setCompany]   = useState('')
  const [jobTitle, setJobTitle]     = useState('')
  const [applicantName, setName]    = useState('')
  const [tone, setTone]             = useState('professional')
  const [loading, setLoading]       = useState(false)
  const [result, setResult]         = useState(null)
  const [editedLetter, setEdited]   = useState('')
  const [letterId, setLetterId]     = useState(null)
  const [saving, setSaving]         = useState(false)

  useEffect(() => {
    sharedAPI.getMyResumes().then((r) => {
      const list = r.data.resumes || []
      setResumes(list)
      if (list.length > 0) setResumeId(list[0].id)
    })
    seekerAPI.getJobs().then((r) => {
      const list = r.data.jobs || []
      setJobs(list)
      if (list.length > 0) setJobId(list[0]._id || list[0].id)
    })
  }, [])

  const handleGenerate = async () => {
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
      const payload = {
        resume_id:      resumeId,
        applicant_name: applicantName || 'Applicant',
        company_name:   companyName || 'the company',
        job_title:      jobTitle    || 'this position',
        tone,
      }

      if (inputType === 'select') {
        payload.job_id = jobId
      } else {
        payload.jd_text = jdText
      }

      const res = await seekerAPI.coverLetter(payload)
      setResult(res.data)
      setEdited(res.data.cover_letter)
      setLetterId(res.data.cover_letter_id)
      toast.success('Cover letter generated!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!letterId) return
    setSaving(true)
    try {
      await seekerAPI.updateCoverLetter(letterId, { edited_text: editedLetter })
      toast.success('Cover letter saved!')
    } catch {
      toast.error('Save failed')
    } finally {
      setSaving(false)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(editedLetter)
    toast.success('Copied to clipboard!')
  }

  const handleDownload = () => {
    const blob = new Blob([editedLetter], { type: 'text/plain' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `cover_letter_${result?.company_name || 'jobmatch'}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const selectStyle = {
    padding: '9px 12px', border: '1px solid var(--gray-300)',
    borderRadius: 'var(--radius)', fontSize: 13, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)',
    width: '100%',
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>AI-Powered Cover Letter Generator</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Generate tailored cover letters incorporating actual skills and experience verified from your resume
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: 24, alignItems: 'start' }}>
        {/* Settings Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Shield size={18} color="var(--primary)" /> Settings
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 4 }}>
                  Select Resume
                </label>
                <select value={resumeId} onChange={(e) => setResumeId(e.target.value)} style={selectStyle}>
                  {resumes.map((r) => (
                    <option key={r.id} value={r.id}>{r.original_filename}</option>
                  ))}
                </select>
              </div>

              <Input
                label="Your Name (optional)"
                placeholder="Auto-detected from resume"
                value={applicantName}
                onChange={(e) => setName(e.target.value)}
              />

              <div style={{ borderTop: '1px solid var(--gray-200)', marginTop: 8, paddingTop: 12 }}>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 6 }}>
                  Target Job Requirement
                </label>
                <div style={{ display: 'flex', border: '1px solid var(--gray-200)', borderRadius: 8, overflow: 'hidden', marginBottom: 12 }}>
                  <button
                    style={{
                      flex: 1, padding: '6px 12px', fontSize: 11, fontWeight: 600, border: 'none', cursor: 'pointer',
                      background: inputType === 'select' ? 'var(--primary-light)' : '#fff',
                      color: inputType === 'select' ? 'var(--primary-dark)' : 'var(--gray-600)'
                    }}
                    onClick={() => setInputType('select')}
                  >
                    Select Job Post
                  </button>
                  <button
                    style={{
                      flex: 1, padding: '6px 12px', fontSize: 11, fontWeight: 600, border: 'none', cursor: 'pointer',
                      background: inputType === 'paste' ? 'var(--primary-light)' : '#fff',
                      color: inputType === 'paste' ? 'var(--primary-dark)' : 'var(--gray-600)'
                    }}
                    onClick={() => setInputType('paste')}
                  >
                    Paste JD Text
                  </button>
                </div>

                {inputType === 'select' ? (
                  <select
                    value={jobId}
                    onChange={(e) => setJobId(e.target.value)}
                    style={selectStyle}
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
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <Input
                      label="Company Name (optional)"
                      placeholder="Auto-detected from JD"
                      value={companyName}
                      onChange={(e) => setCompany(e.target.value)}
                    />
                    <Input
                      label="Job Title (optional)"
                      placeholder="Auto-detected from JD"
                      value={jobTitle}
                      onChange={(e) => setJobTitle(e.target.value)}
                    />
                  </div>
                )}
              </div>

              <div style={{ borderTop: '1px solid var(--gray-200)', marginTop: 8, paddingTop: 12 }}>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 4 }}>
                  Selected Tone
                </label>
                <div style={{ display: 'flex', gap: 6 }}>
                  {TONES.map((t) => (
                    <button key={t} onClick={() => setTone(t)} style={{
                      flex: 1, padding: '8px 4px', borderRadius: 8,
                      border: `2px solid ${tone === t ? 'var(--primary)' : 'var(--gray-200)'}`,
                      background: tone === t ? 'var(--primary-light)' : '#fff',
                      color: tone === t ? 'var(--primary)' : 'var(--gray-600)',
                      fontSize: 11, fontWeight: 600, cursor: 'pointer',
                      textTransform: 'capitalize', transition: 'all 0.15s'
                    }}>
                      {t}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </Card>

          {inputType === 'paste' && (
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 10 }}>Job Description</h3>
              <textarea
                placeholder="Paste the full job description text here..."
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                rows={8}
                style={{
                  width: '100%', padding: '9px 12px', border: '1px solid var(--gray-300)',
                  borderRadius: 8, fontSize: 13, resize: 'vertical', lineHeight: 1.5, fontFamily: 'inherit'
                }}
              />
            </Card>
          )}

          <Button onClick={handleGenerate} loading={loading} fullWidth size="lg">
            <Mail size={16} /> Generate Cover Letter
          </Button>
        </div>

        {/* Results / Outputs Column */}
        <div>
          {result ? (
            <Card style={{ height: '100%' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                <div>
                  <h3 style={{ fontWeight: 600 }}>Your Cover Letter</h3>
                  <p style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 2 }}>
                    {result.word_count} words · Tone: <span style={{ textTransform: 'capitalize' }}>{result.tone}</span>
                  </p>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <Button variant="secondary" size="sm" onClick={handleCopy}>
                    <Copy size={13} /> Copy
                  </Button>
                  <Button variant="secondary" size="sm" onClick={handleDownload}>
                    <Download size={13} /> Download
                  </Button>
                  <Button size="sm" onClick={handleSave} loading={saving}>
                    <Save size={13} /> Save Edits
                  </Button>
                </div>
              </div>

              <textarea
                value={editedLetter}
                onChange={(e) => setEdited(e.target.value)}
                style={{
                  width: '100%', minHeight: 520,
                  padding: '16px', border: '1px solid var(--gray-200)',
                  borderRadius: 8, fontSize: 13,
                  lineHeight: 1.8, resize: 'vertical',
                  fontFamily: 'inherit', color: 'var(--gray-800)',
                  background: 'var(--gray-50)',
                }}
              />

              {/* Matched Skills Metadata */}
              {result.matched_skills_used?.length > 0 && (
                <div style={{ marginTop: 14, borderTop: '1px solid var(--gray-100)', paddingTop: 12 }}>
                  <div style={{ fontSize: 12, color: 'var(--gray-500)', fontWeight: 600, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Star size={13} color="var(--primary)" /> Skills Highlighted from Resume:
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {result.matched_skills_used.map((s) => (
                      <Badge key={s} variant="success" style={{ fontSize: 10 }}>{s}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Relevant Experience Metadata */}
              {result.relevant_experience_used?.years_experience !== null && (
                <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--gray-500)' }}>
                  <span><strong>Years Experience Used:</strong> {result.relevant_experience_used.years_experience} Years</span>
                  <span>•</span>
                  <span><strong>Degree Level Used:</strong> {result.relevant_experience_used.education?.join(', ') || 'Not Specified'}</span>
                </div>
              )}
            </Card>
          ) : (
            <Card style={{
              height: '100%', display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column', gap: 12,
              minHeight: 400,
            }}>
              <HelpCircle size={48} color="var(--gray-300)" />
              <p style={{ color: 'var(--gray-400)', fontSize: 14 }}>
                Choose a resume, select/paste a target requirement and click Generate
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}