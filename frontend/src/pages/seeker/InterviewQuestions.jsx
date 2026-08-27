import { useState, useEffect } from 'react'
import { sharedAPI } from '../../api/shared'
import { seekerAPI } from '../../api/seeker'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Badge from '../../components/ui/Badge'
import { MessageSquare, ChevronDown, ChevronUp, HelpCircle, Shield, Sparkles, Filter, Code } from 'lucide-react'

function QuestionCard({ q }) {
  const [open, setOpen] = useState(false)

  const catColor = (cat) => {
    if (!cat) return 'gray'
    const c = cat.toLowerCase()
    if (c.includes('technical')) return 'info'
    if (c.includes('experience') || c.includes('behavioral')) return 'purple'
    if (c.includes('skills')) return 'warning'
    if (c.includes('job-specific')) return 'success'
    if (c.includes('resume-based')) return 'indigo'
    return 'gray'
  }

  const difficultyVariant = (diff) => {
    if (!diff) return 'gray'
    const d = diff.toLowerCase()
    if (d === 'easy') return 'success'
    if (d === 'medium') return 'warning'
    if (d === 'hard') return 'danger'
    return 'gray'
  }

  return (
    <Card padding="16px" style={{ marginBottom: 12 }}>
      <div style={{ cursor: 'pointer' }} onClick={() => setOpen((p) => !p)}>
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
              <span style={{
                width: 24, height: 24, borderRadius: '50%',
                background: 'var(--primary-light)', color: 'var(--primary)',
                display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 11, fontWeight: 700, flexShrink: 0,
              }}>
                {q.number}
              </span>
              <Badge variant={catColor(q.category)}>{q.category}</Badge>
              <Badge variant={difficultyVariant(q.difficulty)}>{q.difficulty || 'Medium'}</Badge>
              {q.related_skill && (
                <span style={{
                  fontSize: 11, color: 'var(--gray-600)', background: 'var(--gray-100)',
                  padding: '2px 8px', borderRadius: 12, fontWeight: 500, display: 'inline-flex', alignItems: 'center', gap: 4
                }}>
                  <Code size={11} /> {q.related_skill}
                </span>
              )}
            </div>
            <p style={{ fontSize: 14, fontWeight: 600, lineHeight: 1.5, color: 'var(--gray-800)' }}>
              {q.question}
            </p>
          </div>
          {open ? <ChevronUp size={18} color="var(--gray-400)" style={{ flexShrink: 0, marginTop: 4 }} />
                : <ChevronDown size={18} color="var(--gray-400)" style={{ flexShrink: 0, marginTop: 4 }} />}
        </div>
      </div>

      {/* Why Relevant Explanation */}
      {q.why_relevant && (
        <div style={{
          marginTop: 10, padding: '8px 12px', background: '#f8fafc',
          borderRadius: 6, borderLeft: '3px solid var(--primary)',
          fontSize: 12, color: 'var(--gray-600)', lineHeight: 1.4
        }}>
          <strong>Why this question was generated:</strong> {q.why_relevant}
        </div>
      )}

      {open && (
        <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--gray-100)' }}>
          {q.answer_framework && (
            <div style={{ marginBottom: 12 }}>
              <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--primary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
                Answer Framework
              </p>
              <div style={{
                padding: '10px 14px',
                background: 'var(--primary-light)',
                borderRadius: 8,
                fontSize: 13, color: 'var(--gray-700)', lineHeight: 1.6,
              }}>
                {q.answer_framework}
              </div>
            </div>
          )}

          {q.sample_answer && (
            <div>
              <p style={{ fontSize: 11, fontWeight: 700, color: 'var(--success)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 6 }}>
                Sample Answer
              </p>
              <div style={{
                padding: '10px 14px',
                background: '#f0fdf4',
                borderRadius: 8,
                fontSize: 13, color: 'var(--gray-700)', lineHeight: 1.6,
              }}>
                {q.sample_answer}
              </div>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

export default function InterviewQuestions() {
  const [resumes, setResumes]     = useState([])
  const [resumeId, setResumeId]   = useState('')
  const [jobs, setJobs]           = useState([])
  const [jobId, setJobId]         = useState('')
  const [jdText, setJdText]       = useState('')
  const [inputType, setInputType] = useState('select') // 'select' | 'paste'
  const [numQ, setNumQ]           = useState(10)
  const [loading, setLoading]     = useState(false)
  const [result, setResult]       = useState(null)
  const [filter, setFilter]       = useState('all')

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
    if (numQ < 5 || numQ > 20) {
      toast.error('Question count must be between 5 and 20')
      return
    }

    setLoading(true)
    try {
      const payload = {
        resume_id: resumeId,
        num_questions: numQ,
      }
      if (inputType === 'select') {
        payload.job_id = jobId
      } else {
        payload.jd_text = jdText
      }

      const res = await seekerAPI.interviewQuestions(payload)
      setResult(res.data)
      toast.success('Interview questions generated!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Generation failed')
    } finally {
      setLoading(false)
    }
  }

  const categoryOptions = ['all', 'Technical', 'Experience/Behavioral', 'Skills', 'Job-Specific', 'Resume-Based']

  const filteredQuestions = result?.questions?.filter((q) => {
    if (filter === 'all') return true
    return q.category?.toLowerCase().includes(filter.toLowerCase())
  }) || []

  const selectStyle = {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--gray-300)',
    borderRadius: 'var(--radius)', fontSize: 13, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)',
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Intelligent Interview Question Generator</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Generate factual interview questions categorized by difficulty, skill requirements, and resume experience
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 24, alignItems: 'start' }}>
        {/* Controls */}
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
                  {resumes.map((r) => <option key={r.id} value={r.id}>{r.original_filename}</option>)}
                </select>
              </div>

              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)' }}>
                    Number of Questions (5-20)
                  </label>
                  <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--primary)' }}>{numQ}</span>
                </div>
                <input
                  type="range" min={5} max={20} value={numQ}
                  onChange={(e) => setNumQ(Number(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--primary)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--gray-400)' }}>
                  <span>5 Min</span><span>20 Max</span>
                </div>
              </div>

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
                )}
              </div>
            </div>
          </Card>

          <Button onClick={handleGenerate} loading={loading} fullWidth size="lg">
            <MessageSquare size={16} /> Generate Questions
          </Button>

          {/* Preparation Tips */}
          {result?.preparation_tips?.length > 0 && (
            <Card style={{ background: '#f0fdf4', border: '1px solid #bbf7d0' }}>
              <h4 style={{ fontWeight: 600, marginBottom: 8, color: 'var(--success)', fontSize: 13, display: 'flex', alignItems: 'center', gap: 6 }}>
                <Sparkles size={14} /> Preparation Guidelines
              </h4>
              {result.preparation_tips.map((tip, i) => (
                <p key={i} style={{ fontSize: 12, color: 'var(--gray-600)', marginBottom: 6, lineHeight: 1.5 }}>
                  • {tip}
                </p>
              ))}
            </Card>
          )}
        </div>

        {/* Questions Display */}
        <div>
          {result ? (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
                <div>
                  <h3 style={{ fontWeight: 600 }}>
                    {result.total} Questions Generated for {result.job_title}
                  </h3>
                  <p style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 2 }}>
                    Click any question to view answer frameworks and sample responses
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Filter size={14} color="var(--gray-500)" />
                  <select
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    style={{ ...selectStyle, width: 180 }}
                  >
                    {categoryOptions.map((c) => (
                      <option key={c} value={c}>{c === 'all' ? 'All Categories' : c}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                {filteredQuestions.map((q) => <QuestionCard key={q.number} q={q} />)}
                {filteredQuestions.length === 0 && (
                  <Card style={{ padding: 24, textAlign: 'center', color: 'var(--gray-500)' }}>
                    No questions found for the selected category filter.
                  </Card>
                )}
              </div>
            </>
          ) : (
            <Card style={{
              minHeight: 400, display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column', gap: 12,
            }}>
              <HelpCircle size={48} color="var(--gray-300)" />
              <p style={{ color: 'var(--gray-400)', fontSize: 14 }}>
                Configure your target requirement and click Generate Questions
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}