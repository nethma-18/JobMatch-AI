import { useState, useEffect } from 'react'
import { hrAPI } from '../../api/hr'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import ScoreBar from '../../components/ui/ScoreBar'
import { Zap, Trophy, CheckCircle, XCircle, Shield, EyeOff } from 'lucide-react'

export default function JobRanking() {
  const [jobs, setJobs]       = useState([])
  const [jobId, setJobId]     = useState('')
  const [topN, setTopN]       = useState(20)
  const [blindMode, setBlindMode] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult]   = useState(null)

  useEffect(() => {
    hrAPI.getJobs({ status: 'open' }).then((r) => {
      const list = r.data.jobs || []
      setJobs(list)
      if (list.length > 0) setJobId(list[0].id)
    })
  }, [])

  const handleRank = async () => {
    if (!jobId) { toast.error('Select a job post'); return }
    setLoading(true)
    try {
      const res = await hrAPI.rankJob(jobId, topN, blindMode)
      setResult(res.data)
      toast.success(`Ranked ${res.data.total_ranked} candidates!${blindMode ? ' (Blind Mode Active)' : ''}`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Ranking failed — upload CVs for this job first')
    } finally {
      setLoading(false)
    }
  }

  const rankColor = (rank) =>
    rank === 1 ? '#f59e0b' : rank === 2 ? '#9ca3af' : rank === 3 ? '#b45309' : 'var(--gray-400)'

  const rankIcon = (rank) => rank <= 3 ? '🏆' : `#${rank}`

  const selectStyle = {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--gray-300)',
    borderRadius: 10, fontSize: 14, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)',
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Job Ranking</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Rank 500+ CVs against a job description in seconds
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 24 }}>
        {/* Controls */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 14 }}>Settings</h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 6 }}>
                  Select Job Post
                </label>
                <select value={jobId} onChange={(e) => setJobId(e.target.value)} style={selectStyle}>
                  <option value="">-- Select a job --</option>
                  {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
                </select>
              </div>

              <div>
                <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)', display: 'block', marginBottom: 6 }}>
                  Top N Results: {topN}
                </label>
                <input
                  type="range" min={5} max={50} value={topN}
                  onChange={(e) => setTopN(Number(e.target.value))}
                  style={{ width: '100%', accentColor: 'var(--primary)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--gray-400)' }}>
                  <span>5</span><span>50</span>
                </div>
              </div>

              {/* Blind Screening Toggle */}
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
                    Hide candidate names & PII for unbiased review
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

          <Button onClick={handleRank} loading={loading} fullWidth size="lg" disabled={!jobId}>
            <Zap size={16} /> Rank Candidates
          </Button>

          {result && (
            <Card padding="16px">
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {[
                  { label: 'CVs Processed',  value: result.total_cv_processed },
                  { label: 'Ranked',         value: result.total_ranked        },
                  { label: 'Blind Mode',     value: result.blind_mode ? 'Active 🛡️' : 'Off' },
                  { label: 'Time Taken',     value: `${result.processing_time_sec}s` },
                ].map((s) => (
                  <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13 }}>
                    <span style={{ color: 'var(--gray-500)' }}>{s.label}</span>
                    <span style={{ fontWeight: 600 }}>{s.value}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>


        {/* Rankings */}
        <div>
          {result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {result.rankings?.map((candidate) => (
                <Card key={candidate.resume_id} padding="18px">
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                    {/* Rank badge */}
                    <div style={{
                      width: 44, height: 44, borderRadius: '50%',
                      background: candidate.rank <= 3 ? '#fffbeb' : 'var(--gray-100)',
                      border: `2px solid ${rankColor(candidate.rank)}`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: candidate.rank <= 3 ? 18 : 14,
                      fontWeight: 700, color: rankColor(candidate.rank),
                      flexShrink: 0,
                    }}>
                      {rankIcon(candidate.rank)}
                    </div>

                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                        <div>
                          <div style={{ fontWeight: 600, fontSize: 14, display: 'flex', alignItems: 'center', gap: 6 }}>
                            {candidate.candidate_name || candidate.filename}
                            {(candidate.is_anonymized || result.blind_mode) && (
                              <Badge variant="warning" style={{ fontSize: 10, display: 'flex', alignItems: 'center', gap: 3 }}>
                                <Shield size={10} /> Blind Profile
                              </Badge>
                            )}
                          </div>
                          <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 1 }}>
                            {candidate.filename}
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{
                            fontSize: 22, fontWeight: 800,
                            color: candidate.score >= 70 ? 'var(--success)' :
                                   candidate.score >= 45 ? 'var(--warning)' : 'var(--danger)',
                          }}>
                            {Math.round(candidate.score)}%
                          </div>
                          <Badge variant={candidate.interview_eligible ? 'success' : 'gray'}>
                            {candidate.interview_eligible ? '✓ Eligible' : 'Below threshold'}
                          </Badge>
                        </div>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 10 }}>
                        <ScoreBar score={candidate.embedding_score}     label="Semantic match" />
                        <ScoreBar score={candidate.skill_overlap_score} label="Skill overlap"  />
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                        {/* Required Skills */}
                        {(candidate.matched_required_skills?.length > 0 || candidate.missing_required_skills?.length > 0) && (
                          <div style={{ display: 'flex', gap: 12 }}>
                            <div style={{ flex: 1 }}>
                              <div style={{ fontSize: 11, color: 'var(--success)', fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 3 }}>
                                <CheckCircle size={11} /> Required Matched ({candidate.matched_required_skills?.length || 0})
                              </div>
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                {(candidate.matched_required_skills || []).slice(0, 5).map((s) => (
                                  <Badge key={s} variant="success" style={{ fontSize: 10 }}>{s}</Badge>
                                ))}
                              </div>
                            </div>
                            <div style={{ flex: 1 }}>
                              <div style={{ fontSize: 11, color: 'var(--danger)', fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 3 }}>
                                <XCircle size={11} /> Required Missing ({candidate.missing_required_skills?.length || 0})
                              </div>
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                {(candidate.missing_required_skills || []).slice(0, 5).map((s) => (
                                  <Badge key={s} variant="danger" style={{ fontSize: 10 }}>{s}</Badge>
                                ))}
                              </div>
                            </div>
                          </div>
                        )}

                        {/* Preferred Skills */}
                        {(candidate.matched_preferred_skills?.length > 0 || candidate.missing_preferred_skills?.length > 0) && (
                          <div style={{ display: 'flex', gap: 12, borderTop: '1px solid var(--gray-100)', paddingTop: 8 }}>
                            <div style={{ flex: 1 }}>
                              <div style={{ fontSize: 11, color: 'var(--success)', fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 3 }}>
                                <CheckCircle size={11} /> Preferred Matched ({candidate.matched_preferred_skills?.length || 0})
                              </div>
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                {(candidate.matched_preferred_skills || []).slice(0, 5).map((s) => (
                                  <Badge key={s} variant="success" style={{ fontSize: 10 }}>{s}</Badge>
                                ))}
                              </div>
                            </div>
                            <div style={{ flex: 1 }}>
                              <div style={{ fontSize: 11, color: 'var(--gray-500)', fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 3 }}>
                                <XCircle size={11} /> Preferred Missing ({candidate.missing_preferred_skills?.length || 0})
                              </div>
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                                {(candidate.missing_preferred_skills || []).slice(0, 5).map((s) => (
                                  <Badge key={s} variant="gray" style={{ fontSize: 10 }}>{s}</Badge>
                                ))}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Card style={{
              minHeight: 400, display: 'flex',
              alignItems: 'center', justifyContent: 'center',
              flexDirection: 'column', gap: 12,
            }}>
              <Trophy size={48} color="var(--gray-300)" />
              <p style={{ color: 'var(--gray-400)', fontSize: 14 }}>
                Select a job and click Rank Candidates
              </p>
              <p style={{ color: 'var(--gray-400)', fontSize: 12 }}>
                Upload CVs via Bulk Upload first
              </p>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}