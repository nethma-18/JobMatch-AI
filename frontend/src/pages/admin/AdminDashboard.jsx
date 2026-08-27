import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminAPI } from '../../api/admin'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import { fmtDate } from '../../utils/helpers'
import {
  CheckSquare, Database, BarChart2,
  ArrowRight, RefreshCw, AlertTriangle,
  Users, FileText, Briefcase, Zap,
} from 'lucide-react'

export default function AdminDashboard() {
  const navigate = useNavigate()
  const [stats, setStats]       = useState(null)
  const [platform, setPlatform] = useState(null)
  const [logs, setLogs]         = useState([])
  const [retraining, setRetraining] = useState(false)
  const [loading, setLoading]   = useState(true)

  const load = async () => {
    try {
      const [v, p, l] = await Promise.all([
        adminAPI.getValidationStats(),
        adminAPI.getPlatformStats(),
        adminAPI.getRetrainLogs(),
      ])
      setStats(v.data)
      setPlatform(p.data)
      setLogs(l.data || [])
    } catch {} finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  const handleRetrain = async () => {
    if (!confirm('Start model retraining now? This may take a few minutes.')) return
    setRetraining(true)
    try {
      await adminAPI.retrain()
      alert('Retraining complete!')
      load()
    } catch {
      alert('Retraining failed — check logs')
    } finally {
      setRetraining(false)
    }
  }

  const features = [
    { label: 'Review Queue',   icon: CheckSquare, to: '/admin/queue', desc: `${stats?.pending_admin_review || 0} pending reviews`, color: 'var(--warning)'  },
    { label: 'Training Pool',  icon: Database,    to: '/admin/pool',  desc: `${platform?.content?.training_pool_size || 0} documents`, color: 'var(--primary)' },
    { label: 'Platform Stats', icon: BarChart2,   to: '/admin/stats', desc: 'Users, content, activity', color: 'var(--info)'    },
  ]

  return (
    <div>
      <div style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Admin Dashboard</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Validation queue, training pool, and platform management
        </p>
      </div>

      {/* Feature cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16, marginBottom: 28 }}>
        {features.map(({ label, icon: Icon, to, desc, color }) => (
          <Card
            key={to} padding="22px"
            style={{ cursor: 'pointer' }}
            onClick={() => navigate(to)}
          >
            <div style={{
              width: 42, height: 42, borderRadius: 10,
              background: `${color}18`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 12,
            }}>
              <Icon size={20} color={color} />
            </div>
            <div style={{ fontWeight: 600, fontSize: 15 }}>{label}</div>
            <div style={{ fontSize: 13, color: 'var(--gray-500)', marginTop: 4 }}>{desc}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 12, color, fontSize: 12 }}>
              Open <ArrowRight size={12} />
            </div>
          </Card>
        ))}
      </div>

      {/* Validation stats */}
      {stats && (
        <>
          <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 14 }}>Validation Pipeline</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
            {[
              { label: 'Total Uploads',    value: stats.total_uploads,        color: 'var(--gray-700)' },
              { label: 'Auto Approved',    value: `${stats.auto_approved} (${stats.auto_approve_rate}%)`, color: 'var(--success)' },
              { label: 'Auto Rejected',    value: `${stats.auto_rejected} (${stats.auto_reject_rate}%)`, color: 'var(--danger)'  },
              { label: 'Pending Review',   value: stats.pending_admin_review,  color: 'var(--warning)' },
            ].map((s) => (
              <Card key={s.label} padding="18px">
                <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 4 }}>{s.label}</div>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* Platform stats */}
      {platform && (
        <>
          <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 14 }}>Platform Overview</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 28 }}>
            {[
              { label: 'Total Users',     value: platform.users?.total,            icon: Users,     color: 'var(--primary)' },
              { label: 'Job Seekers',     value: platform.users?.seekers,           icon: Users,     color: 'var(--info)'    },
              { label: 'HR Recruiters',   value: platform.users?.hr,                icon: Briefcase, color: 'var(--warning)' },
              { label: 'New (7 days)',    value: platform.users?.new_last_7_days,   icon: Users,     color: 'var(--success)' },
              { label: 'Resumes',         value: platform.content?.total_resumes,   icon: FileText,  color: 'var(--gray-700)' },
              { label: 'Job Posts',       value: platform.content?.total_job_posts, icon: Briefcase, color: 'var(--gray-700)' },
              { label: 'Rankings Run',    value: platform.content?.total_rankings,  icon: BarChart2, color: 'var(--gray-700)' },
              { label: 'Training Docs',   value: platform.content?.training_pool_size, icon: Database, color: 'var(--primary)' },
            ].map((s) => (
              <Card key={s.label} padding="16px">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <s.icon size={16} color={s.color} />
                  <span style={{ fontSize: 12, color: 'var(--gray-500)' }}>{s.label}</span>
                </div>
                <div style={{ fontSize: 22, fontWeight: 700, color: s.color }}>{s.value ?? '—'}</div>
              </Card>
            ))}
          </div>
        </>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Manual retrain */}
        <Card>
          <h3 style={{ fontWeight: 600, marginBottom: 6 }}>Model Retraining</h3>
          <p style={{ fontSize: 13, color: 'var(--gray-500)', marginBottom: 16, lineHeight: 1.6 }}>
            Automatic retraining runs every Sunday at 02:00 UTC.
            Click below to trigger manual retraining using current training pool data.
          </p>
          <Button onClick={handleRetrain} loading={retraining} fullWidth>
            <Zap size={15} /> Retrain Now
          </Button>
        </Card>

        {/* Retrain logs */}
        <Card>
          <h3 style={{ fontWeight: 600, marginBottom: 12 }}>Recent Retrain Logs</h3>
          {logs.length === 0 ? (
            <p style={{ fontSize: 13, color: 'var(--gray-400)' }}>No retraining runs yet</p>
          ) : logs.slice(0, 4).map((log, i) => (
            <div key={log.id || i} style={{
              display: 'flex', justifyContent: 'space-between',
              padding: '8px 0',
              borderBottom: i < Math.min(logs.length, 4) - 1 ? '1px solid var(--gray-100)' : 'none',
              fontSize: 13,
            }}>
              <div>
                <Badge variant={
                  log.status === 'completed' ? 'success' :
                  log.status === 'failed'    ? 'danger'  : 'warning'
                }>
                  {log.status}
                </Badge>
                <span style={{ marginLeft: 8, color: 'var(--gray-600)' }}>
                  {log.training_data_count} docs
                  {log.new_skills_added ? ` · +${log.new_skills_added} skills` : ''}
                </span>
              </div>
              <span style={{ color: 'var(--gray-400)', fontSize: 12 }}>
                {fmtDate(log.retraining_started_at)}
              </span>
            </div>
          ))}
        </Card>
      </div>
    </div>
  )
}