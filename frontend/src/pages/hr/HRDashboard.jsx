import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { hrAPI } from '../../api/hr'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import ScoreCircle from '../../components/ui/ScoreCircle'
import { fmtDate, statusBadge } from '../../utils/helpers'
import {
  Briefcase, Upload, List, Star,
  Calendar, BarChart2, Users, ArrowRight,
  TrendingUp, FileText, Sparkles, Building2, Plus,
} from 'lucide-react'

const features = [
  { label: 'Job Posts',     icon: Briefcase,  to: '/hr/jobs',       desc: 'Create, edit & manage job listings'     },
  { label: 'Bulk Upload',   icon: Upload,      to: '/hr/upload',     desc: 'Batch upload candidate CVs (PDF/DOCX)' },
  { label: 'Job Ranking',   icon: List,        to: '/hr/ranking',    desc: 'AI candidate ranking & match scores'   },
  { label: 'Shortlist',     icon: Star,        to: '/hr/shortlist',  desc: 'Manage candidate shortlists'           },
  { label: 'Skill Gap',     icon: TrendingUp,  to: '/hr/skill-gap',  desc: 'Skill gap breakdown & development'     },
  { label: 'Interviews',    icon: Calendar,    to: '/hr/interviews', desc: 'Schedule & track candidate interviews' },
  { label: 'Analytics',     icon: BarChart2,   to: '/hr/analytics',  desc: 'Hiring pipeline metrics & insights'    },
  { label: 'Team & Collab', icon: Users,       to: '/hr/collab',     desc: 'Team reviews, votes & notes'           },
]

export default function HRDashboard() {
  const { user } = useAuth()
  const navigate  = useNavigate()
  const [overview, setOverview] = useState(null)
  const [jobs, setJobs]         = useState([])
  const [upcoming, setUpcoming] = useState([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    Promise.all([
      hrAPI.getAnalytics(),
      hrAPI.getJobs({ limit: 5 }),
      hrAPI.getUpcoming(),
    ]).then(([a, j, u]) => {
      setOverview(a.data.overview)
      setJobs(j.data.jobs || [])
      setUpcoming(u.data || [])
    }).catch(() => {}).finally(() => setLoading(false))
  }, [])

  const avgScoreNum = overview?.average_match_score || 76

  const overviewCards = [
    { label: 'Open Positions',    value: overview?.open_jobs        || 0, color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)' },
    { label: 'CVs Processed',     value: overview?.total_cv_processed || 0, color: '#6366f1', bg: 'rgba(99, 102, 241, 0.12)' },
    { label: 'Shortlisted',       value: overview?.total_shortlisted  || 0, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)' },
    { label: 'Avg AI Match',      value: overview?.average_match_score ? `${overview.average_match_score}%` : '76%', color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.12)' },
  ]

  return (
    <div>
      {/* Spotify-inspired Recruiter Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(16, 185, 129, 0.15) 100%)',
        border: '1px solid var(--card-border, #334155)',
        borderRadius: 'var(--radius-lg, 20px)',
        padding: '32px 36px',
        marginBottom: 28,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 20,
        boxShadow: 'var(--shadow-glow)',
      }}>
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '4px 12px', borderRadius: 999, background: 'var(--primary-light)', color: 'var(--primary)', fontSize: 12, fontWeight: 600, marginBottom: 12 }}>
            <Building2 size={14} /> {user?.company_name || 'Recruiter Portal'}
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: 'var(--gray-900)', letterSpacing: '-0.02em' }}>
            Welcome, {user?.name?.split(' ')[0]} 👋
          </h1>
          <p style={{ color: 'var(--gray-500)', marginTop: 6, fontSize: 14, maxWidth: 520 }}>
            Rank candidates using AI matching, analyze skill gaps, and streamline your recruitment pipeline.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16, background: 'var(--card-bg, #1e293b)', padding: '14px 20px', borderRadius: 'var(--radius)', border: '1px solid var(--card-border, #334155)' }}>
            <ScoreCircle score={avgScoreNum} size={65} strokeWidth={6} label="" />
            <div>
              <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--gray-400)', fontWeight: 600 }}>Avg Match Score</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--gray-900)', marginTop: 2 }}>
                {avgScoreNum}% Pool Match
              </div>
              <span style={{ fontSize: 11, color: 'var(--success)', fontWeight: 600 }}>High Compatibility</span>
            </div>
          </div>

          <Button onClick={() => navigate('/hr/jobs')} pill size="lg">
            <Plus size={16} /> Post New Job
          </Button>
        </div>
      </div>

      {/* Overview Stat Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        {overviewCards.map((s) => (
          <Card key={s.label} padding="22px" hoverable>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: 32, fontWeight: 800, color: s.color, lineHeight: 1.1 }}>{s.value}</div>
                <div style={{ fontSize: 13, color: 'var(--gray-500)', marginTop: 6, fontWeight: 500 }}>{s.label}</div>
              </div>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: s.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Sparkles size={20} color={s.color} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* HR Tools Grid */}
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--gray-900)' }}>Recruitment Tools</h2>
        <span style={{ fontSize: 12, color: 'var(--gray-500)', fontWeight: 500 }}>8 AI Modules Active</span>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16, marginBottom: 36 }}>
        {features.map(({ label, icon: Icon, to, desc }) => (
          <Card
            key={to} padding="22px"
            hoverable
            onClick={() => navigate(to)}
            style={{ cursor: 'pointer' }}
          >
            <div style={{
              width: 42, height: 42, borderRadius: 12,
              background: 'var(--primary-light)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 14,
            }}>
              <Icon size={20} color="var(--primary)" />
            </div>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--gray-900)' }}>{label}</div>
            <div style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 4, lineHeight: 1.4, minHeight: 34 }}>{desc}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 14, color: 'var(--primary)', fontSize: 12, fontWeight: 600 }}>
              Open Module <ArrowRight size={13} />
            </div>
          </Card>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20 }}>
        {/* Recent Jobs */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--gray-900)' }}>Recent Job Posts</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/hr/jobs')}>
              View All <ArrowRight size={13} />
            </Button>
          </div>
          <Card padding="0">
            {jobs.length === 0 ? (
              <div style={{ padding: 28, textAlign: 'center', color: 'var(--gray-400)', fontSize: 13 }}>
                No job posts created yet. <span style={{ color: 'var(--primary)', cursor: 'pointer', fontWeight: 600 }} onClick={() => navigate('/hr/jobs')}>Create your first post</span>
              </div>
            ) : jobs.map((j, i) => (
              <div key={j.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '16px 20px',
                borderBottom: i < jobs.length - 1 ? '1px solid var(--card-border, #334155)' : 'none',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--primary-light)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Briefcase size={18} color="var(--primary)" />
                  </div>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--gray-900)' }}>{j.title}</div>
                    <div style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 2 }}>
                      {j.location || 'Remote'} · {fmtDate(j.created_at)}
                    </div>
                  </div>
                </div>
                <Badge variant={statusBadge(j.status)}>{j.status}</Badge>
              </div>
            ))}
          </Card>
        </div>

        {/* Upcoming Interviews */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--gray-900)' }}>Upcoming Interviews</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/hr/interviews')}>
              View All <ArrowRight size={13} />
            </Button>
          </div>
          <Card padding="0">
            {upcoming.length === 0 ? (
              <div style={{ padding: 28, textAlign: 'center', color: 'var(--gray-400)', fontSize: 13 }}>
                No upcoming interviews scheduled in the next 7 days.
              </div>
            ) : upcoming.map((iv, i) => (
              <div key={iv.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '16px 20px',
                borderBottom: i < upcoming.length - 1 ? '1px solid var(--card-border, #334155)' : 'none',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(245, 158, 11, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Calendar size={18} color="#f59e0b" />
                  </div>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--gray-900)' }}>
                      Interview · {fmtDate(iv.scheduled_date)}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 2 }}>
                      {iv.duration_minutes} min · {iv.meeting_link ? 'Online Video' : 'On-site'}
                    </div>
                  </div>
                </div>
                <Badge variant={statusBadge(iv.status)}>{iv.status}</Badge>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </div>
  )
}