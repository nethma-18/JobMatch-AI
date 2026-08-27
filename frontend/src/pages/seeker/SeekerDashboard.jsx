import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { seekerAPI } from '../../api/seeker'
import { sharedAPI } from '../../api/shared'
import Card from '../../components/ui/Card'
import Badge from '../../components/ui/Badge'
import Button from '../../components/ui/Button'
import ScoreCircle from '../../components/ui/ScoreCircle'
import { statusBadge, fmtDate } from '../../utils/helpers'
import {
  TrendingUp, CheckSquare, AlertCircle, Mail,
  MessageSquare, Briefcase, Upload, ArrowRight, Sparkles, UserCheck,
} from 'lucide-react'

const features = [
  { label: 'Resume Enhancer',      icon: TrendingUp,    to: '/seeker/enhancer',     desc: 'Get your AI match score & eligibility'    },
  { label: 'ATS Checker',          icon: CheckSquare,   to: '/seeker/ats',           desc: 'Check ATS format compatibility'          },
  { label: 'Rejection Diagnostic', icon: AlertCircle,   to: '/seeker/diagnostic',    desc: 'Identify skill gaps & rejection reasons' },
  { label: 'Cover Letter',         icon: Mail,          to: '/seeker/cover-letter',  desc: 'Generate tailored AI cover letters'      },
  { label: 'Interview Q&A',        icon: MessageSquare, to: '/seeker/interview-q',   desc: 'Role-specific interview questions'      },
  { label: 'Job Tracker',          icon: Briefcase,     to: '/seeker/tracker',       desc: 'Track your application status'           },
]

export default function SeekerDashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [stats, setStats]     = useState(null)
  const [resumes, setResumes] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      seekerAPI.getStats(),
      sharedAPI.getMyResumes(),
    ]).then(([s, r]) => {
      setStats(s.data)
      setResumes(r.data.resumes || [])
    }).finally(() => setLoading(false))
  }, [])

  const statCards = [
    { label: 'Applications', value: stats?.applied   || 0, color: '#3b82f6', bg: 'rgba(59, 130, 246, 0.12)' },
    { label: 'Interviews',   value: stats?.interview  || 0, color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)' },
    { label: 'Job Offers',   value: stats?.offer      || 0, color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)' },
    { label: 'Rejections',   value: stats?.rejected   || 0, color: '#ef4444', bg: 'rgba(239, 68, 68, 0.12)' },
  ]

  const latestResume = resumes[0]

  return (
    <div>
      {/* Spotify-inspired Banner Header */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(168, 85, 247, 0.15) 100%)',
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
            <Sparkles size={14} /> JobMatch AI Seeker Hub
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: 'var(--gray-900)', letterSpacing: '-0.02em' }}>
            Welcome back, {user?.name?.split(' ')[0]} 👋
          </h1>
          <p style={{ color: 'var(--gray-500)', marginTop: 6, fontSize: 14, maxWidth: 500 }}>
            Optimize your resume, analyze ATS compatibility, and land top developer & tech roles.
          </p>
        </div>

        {latestResume ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 18, background: 'var(--card-bg, #1e293b)', padding: '16px 20px', borderRadius: 'var(--radius)', border: '1px solid var(--card-border, #334155)' }}>
            <ScoreCircle score={latestResume.char_count > 500 ? 88 : 65} size={70} strokeWidth={6} label="" />
            <div>
              <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--gray-400)', fontWeight: 600 }}>Active CV</div>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--gray-900)', marginTop: 2, maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {latestResume.original_filename}
              </div>
              <Badge variant={latestResume.validation_status === 'auto_approved' ? 'success' : 'gray'} style={{ marginTop: 6 }}>
                {latestResume.validation_status}
              </Badge>
            </div>
          </div>
        ) : (
          <Button onClick={() => navigate('/seeker/enhancer')} pill size="lg">
            <Upload size={16} /> Upload Resume Now
          </Button>
        )}
      </div>

      {/* Upload resume CTA if empty */}
      {resumes.length === 0 && (
        <Card style={{ marginBottom: 28, background: 'var(--primary-light)', border: '1px solid var(--primary)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 14 }}>
            <div>
              <p style={{ fontWeight: 700, color: 'var(--primary-dark)', fontSize: 15 }}>Upload your resume to get started</p>
              <p style={{ fontSize: 13, color: 'var(--gray-600)', marginTop: 2 }}>
                Upload once — use seamlessly across all 6 AI career tools
              </p>
            </div>
            <Button onClick={() => navigate('/seeker/enhancer')}>
              <Upload size={15} /> Upload Resume
            </Button>
          </div>
        </Card>
      )}

      {/* Overview Stat Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 32 }}>
        {statCards.map((s) => (
          <Card key={s.label} padding="22px" hoverable>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: 32, fontWeight: 800, color: s.color, lineHeight: 1.1 }}>{s.value}</div>
                <div style={{ fontSize: 13, color: 'var(--gray-500)', marginTop: 6, fontWeight: 500 }}>{s.label}</div>
              </div>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: s.bg, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <UserCheck size={20} color={s.color} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* AI Tool Grid */}
      <div style={{ marginBottom: 16, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--gray-900)' }}>AI Career Tools</h2>
        <span style={{ fontSize: 12, color: 'var(--gray-500)', fontWeight: 500 }}>6 Intelligence Engines Available</span>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginBottom: 36 }}>
        {features.map(({ label, icon: Icon, to, desc }) => (
          <Card
            key={to}
            padding="24px"
            hoverable
            onClick={() => navigate(to)}
            style={{ cursor: 'pointer' }}
          >
            <div style={{
              width: 44, height: 44, borderRadius: 12,
              background: 'var(--primary-light)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 16,
            }}>
              <Icon size={22} color="var(--primary)" />
            </div>
            <div style={{ fontWeight: 700, fontSize: 15, color: 'var(--gray-900)' }}>{label}</div>
            <div style={{ fontSize: 13, color: 'var(--gray-500)', marginTop: 6, lineHeight: 1.5, minHeight: 38 }}>{desc}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 16, color: 'var(--primary)', fontSize: 13, fontWeight: 600 }}>
              Launch Tool <ArrowRight size={14} />
            </div>
          </Card>
        ))}
      </div>

      {/* Recent Resumes */}
      {resumes.length > 0 && (
        <>
          <div style={{ marginBottom: 14, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--gray-900)' }}>My Uploaded Resumes</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate('/seeker/resumes')}>
              View All <ArrowRight size={14} />
            </Button>
          </div>
          <Card padding="0">
            {resumes.slice(0, 5).map((r, i) => (
              <div key={r.id} style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                padding: '16px 24px',
                borderBottom: i < resumes.length - 1 ? '1px solid var(--card-border, #334155)' : 'none',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                  <div style={{ width: 38, height: 38, borderRadius: 10, background: 'var(--primary-light)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Sparkles size={18} color="var(--primary)" />
                  </div>
                  <div>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--gray-900)' }}>{r.original_filename}</div>
                    <div style={{ fontSize: 12, color: 'var(--gray-500)', marginTop: 2 }}>
                      Uploaded {fmtDate(r.uploaded_at)} · {r.char_count?.toLocaleString()} characters
                    </div>
                  </div>
                </div>
                <Badge variant={r.validation_status === 'auto_approved' ? 'success' : 'gray'}>
                  {r.validation_status}
                </Badge>
              </div>
            ))}
          </Card>
        </>
      )}
    </div>
  )
}