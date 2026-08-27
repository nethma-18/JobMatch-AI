import { useState, useEffect } from 'react'
import { hrAPI } from '../../api/hr'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'
import Badge from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import { Users, Plus, MessageSquare, ThumbsUp, ThumbsDown, Minus } from 'lucide-react'

export default function CollabHiring() {
  const [team, setTeam]         = useState([])
  const [jobs, setJobs]         = useState([])
  const [jobId, setJobId]       = useState('')
  const [rankings, setRankings] = useState([])
  const [selectedCand, setCand] = useState(null)
  const [reviews, setReviews]   = useState(null)
  const [memberModal, setMemberModal] = useState(false)
  const [memberEmail, setMemberEmail] = useState('')
  const [comment, setComment]   = useState('')
  const [rating, setRating]     = useState(5)
  const [saving, setSaving]     = useState(false)

  useEffect(() => {
    Promise.all([hrAPI.getTeamMembers(), hrAPI.getJobs({ status: 'open' })]).then(([t, j]) => {
      setTeam(t.data.team_members || [])
      const list = j.data.jobs || []
      setJobs(list)
      if (list.length > 0) setJobId(list[0].id)
    })
  }, [])

  useEffect(() => {
    if (!jobId) return
    hrAPI.getRankings(jobId)
      .then((r) => setRankings(r.data?.rankings || []))
      .catch(() => setRankings([]))
  }, [jobId])

  useEffect(() => {
    if (!selectedCand || !jobId) return
    hrAPI.getComments(jobId, selectedCand.resume_id)
      .then((r) => setReviews(r.data))
      .catch(() => setReviews(null))
  }, [selectedCand, jobId])

  const handleAddMember = async () => {
    if (!memberEmail) return
    setSaving(true)
    try {
      await hrAPI.addTeamMember({ member_email: memberEmail, role: 'reviewer' })
      toast.success('Team member added!')
      setMemberEmail('')
      setMemberModal(false)
      const t = await hrAPI.getTeamMembers()
      setTeam(t.data.team_members || [])
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add member')
    } finally { setSaving(false) }
  }

  const handleComment = async () => {
    if (!comment.trim() || !selectedCand) return
    try {
      await hrAPI.addComment(jobId, {
        candidate_id: selectedCand.resume_id,
        comment, rating,
      })
      toast.success('Comment added')
      setComment('')
      const r = await hrAPI.getComments(jobId, selectedCand.resume_id)
      setReviews(r.data)
    } catch { toast.error('Failed to add comment') }
  }

  const handleVote = async (vote) => {
    if (!selectedCand) return
    try {
      const res = await hrAPI.castVote(jobId, {
        candidate_id: selectedCand.resume_id, vote,
      })
      toast.success(`Vote: ${vote}`)
      const tally = res.data.tally
      setReviews((p) => ({ ...p, votes_tally: tally }))
    } catch { toast.error('Vote failed') }
  }

  const selectStyle = {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--gray-300)',
    borderRadius: 10, fontSize: 14, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)',
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Collaborative Hiring</h1>
          <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>Team reviews, comments, and voting</p>
        </div>
        <Button onClick={() => setMemberModal(true)}><Plus size={15} /> Add Team Member</Button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 20 }}>
        {/* Left panel */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {/* Team members */}
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 12, fontSize: 14 }}>
              Team ({team.length})
            </h3>
            {team.length === 0 ? (
              <p style={{ fontSize: 12, color: 'var(--gray-400)' }}>No team members yet</p>
            ) : team.map((m, i) => (
              <div key={i} style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '6px 0',
                borderBottom: i < team.length - 1 ? '1px solid var(--gray-100)' : 'none',
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: 'var(--primary-light)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 11, fontWeight: 700, color: 'var(--primary)',
                }}>
                  {m.email?.[0]?.toUpperCase()}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 12, fontWeight: 500 }}>{m.email}</div>
                  <div style={{ fontSize: 10, color: 'var(--gray-400)' }}>{m.role}</div>
                </div>
              </div>
            ))}
          </Card>

          {/* Job selector */}
          <Card>
            <h3 style={{ fontWeight: 600, marginBottom: 10, fontSize: 14 }}>Job Post</h3>
            <select value={jobId} onChange={(e) => { setJobId(e.target.value); setCand(null) }} style={selectStyle}>
              {jobs.map((j) => <option key={j.id} value={j.id}>{j.title}</option>)}
            </select>
          </Card>

          {/* Candidates */}
          {rankings.length > 0 && (
            <Card>
              <h3 style={{ fontWeight: 600, marginBottom: 10, fontSize: 14 }}>Candidates</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {rankings.slice(0, 10).map((c) => (
                  <div
                    key={c.resume_id}
                    onClick={() => setCand(c)}
                    style={{
                      padding: '8px 10px', borderRadius: 8,
                      border: `2px solid ${selectedCand?.resume_id === c.resume_id ? 'var(--primary)' : 'var(--gray-200)'}`,
                      background: selectedCand?.resume_id === c.resume_id ? 'var(--primary-light)' : '#fff',
                      cursor: 'pointer', fontSize: 12,
                    }}
                  >
                    <div style={{ fontWeight: 500 }}>#{c.rank} {c.candidate_name || c.filename}</div>
                    <div style={{ color: 'var(--gray-400)', marginTop: 1 }}>{Math.round(c.score)}% match</div>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* Right — Review panel */}
        <div>
          {selectedCand ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Candidate header */}
              <Card>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h3 style={{ fontWeight: 600 }}>{selectedCand.candidate_name || selectedCand.filename}</h3>
                    <p style={{ fontSize: 13, color: 'var(--gray-500)', marginTop: 2 }}>
                      Rank #{selectedCand.rank} · {Math.round(selectedCand.score)}% match
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: 10 }}>
                    <Button size="sm" variant="secondary" onClick={() => handleVote('hire')}>
                      <ThumbsUp size={13} /> Hire
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => handleVote('maybe')}>
                      <Minus size={13} /> Maybe
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => handleVote('reject')}>
                      <ThumbsDown size={13} /> Reject
                    </Button>
                  </div>
                </div>

                {/* Vote tally */}
                {reviews?.votes_tally && (
                  <div style={{ display: 'flex', gap: 16, marginTop: 14, padding: '10px 0', borderTop: '1px solid var(--gray-100)' }}>
                    {[
                      { label: 'Hire',   value: reviews.votes_tally.hire   || 0, color: 'var(--success)' },
                      { label: 'Maybe',  value: reviews.votes_tally.maybe  || 0, color: 'var(--warning)' },
                      { label: 'Reject', value: reviews.votes_tally.reject || 0, color: 'var(--danger)'  },
                    ].map((v) => (
                      <div key={v.label} style={{ textAlign: 'center' }}>
                        <div style={{ fontSize: 20, fontWeight: 700, color: v.color }}>{v.value}</div>
                        <div style={{ fontSize: 11, color: 'var(--gray-400)' }}>{v.label}</div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              {/* Add comment */}
              <Card>
                <h3 style={{ fontWeight: 600, marginBottom: 12, fontSize: 14 }}>
                  <MessageSquare size={15} style={{ marginRight: 6 }} />
                  Add Review
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  <Input
                    rows={3}
                    placeholder="Share your thoughts about this candidate..."
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                  />
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)' }}>
                      Rating: {rating}/5
                    </label>
                    <input
                      type="range" min={1} max={5} value={rating}
                      onChange={(e) => setRating(Number(e.target.value))}
                      style={{ flex: 1, accentColor: 'var(--primary)' }}
                    />
                  </div>
                  <Button onClick={handleComment} size="sm" disabled={!comment.trim()}>
                    Submit Review
                  </Button>
                </div>
              </Card>

              {/* Comments list */}
              <Card>
                <h3 style={{ fontWeight: 600, marginBottom: 12, fontSize: 14 }}>
                  Reviews ({reviews?.comments?.length || 0})
                </h3>
                {!reviews?.comments?.length ? (
                  <p style={{ fontSize: 13, color: 'var(--gray-400)' }}>No reviews yet for this candidate</p>
                ) : reviews.comments.map((c, i) => (
                  <div key={i} style={{
                    padding: '12px 0',
                    borderBottom: i < reviews.comments.length - 1 ? '1px solid var(--gray-100)' : 'none',
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: 13, fontWeight: 500 }}>
                        {c.reviewer_name || 'Reviewer'}
                      </span>
                      {c.rating && (
                        <span style={{ fontSize: 12, color: 'var(--warning)' }}>
                          {'★'.repeat(c.rating)}{'☆'.repeat(5 - c.rating)}
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: 13, color: 'var(--gray-600)', lineHeight: 1.5 }}>{c.comment}</p>
                  </div>
                ))}
              </Card>
            </div>
          ) : (
            <Card style={{ minHeight: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 12 }}>
              <Users size={44} color="var(--gray-300)" />
              <p style={{ color: 'var(--gray-400)', fontSize: 14 }}>Select a candidate to review</p>
            </Card>
          )}
        </div>
      </div>

      {/* Add Member Modal */}
      <Modal open={memberModal} onClose={() => setMemberModal(false)} title="Add Team Member" width={400}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Input
            label="Member Email"
            type="email"
            value={memberEmail}
            onChange={(e) => setMemberEmail(e.target.value)}
            placeholder="colleague@company.com"
          />
          <p style={{ fontSize: 12, color: 'var(--gray-500)' }}>
            The user must already have an account in JobMatch AI.
          </p>
          <div style={{ display: 'flex', gap: 10 }}>
            <Button variant="secondary" fullWidth onClick={() => setMemberModal(false)}>Cancel</Button>
            <Button fullWidth onClick={handleAddMember} loading={saving}>Add Member</Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}