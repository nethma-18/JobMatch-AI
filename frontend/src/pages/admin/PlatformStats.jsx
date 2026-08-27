import { useState, useEffect } from 'react'
import { adminAPI } from '../../api/admin'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import { fmtDate } from '../../utils/helpers'
import {
  Users, FileText, Briefcase,
  BarChart2, Database, UserCheck, UserX,
} from 'lucide-react'

export default function PlatformStats() {
  const [platform, setPlatform] = useState(null)
  const [valStats, setValStats] = useState(null)
  const [users, setUsers]       = useState([])
  const [loading, setLoading]   = useState(true)
  const [userRole, setUserRole] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const [p, v] = await Promise.all([
        adminAPI.getPlatformStats(),
        adminAPI.getValidationStats(),
      ])
      setPlatform(p.data)
      setValStats(v.data)
    } catch {} finally { setLoading(false) }
  }

  const loadUsers = async () => {
    try {
      const params = {}
      if (userRole) params.role = userRole
      const res = await adminAPI.getUsers(params)
      setUsers(res.data.users || [])
    } catch {}
  }

  useEffect(() => { load() }, [])
  useEffect(() => { loadUsers() }, [userRole])

  const handleDeactivate = async (userId, active) => {
    try {
      if (active) {
        await adminAPI.deactivateUser(userId)
        toast.success('User deactivated')
      } else {
        await adminAPI.activateUser(userId)
        toast.success('User activated')
      }
      loadUsers()
    } catch { toast.error('Action failed') }
  }

  if (loading) return (
    <p style={{ padding: 40, textAlign: 'center', color: 'var(--gray-400)' }}>
      Loading platform stats...
    </p>
  )

  const selectStyle = {
    padding: '8px 12px', border: '1px solid var(--gray-300)',
    borderRadius: 8, fontSize: 13, background: 'var(--input-bg, #fff)', color: 'var(--gray-800)', cursor: 'pointer',
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>Platform Statistics</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>
          Users, content, and system-wide metrics
        </p>
      </div>

      {/* User stats */}
      {platform?.users && (
        <>
          <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>Users</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 24 }}>
            {[
              { label: 'Total Users',    value: platform.users.total,           icon: Users,    color: 'var(--primary)' },
              { label: 'Job Seekers',    value: platform.users.seekers,          icon: Users,    color: 'var(--info)'    },
              { label: 'HR Recruiters', value: platform.users.hr,               icon: Briefcase,color: 'var(--warning)' },
              { label: 'New (7 days)',  value: platform.users.new_last_7_days,  icon: UserCheck,color: 'var(--success)' },
            ].map((s) => (
              <Card key={s.label} padding="18px">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <s.icon size={18} color={s.color} />
                  <span style={{ fontSize: 12, color: 'var(--gray-500)' }}>{s.label}</span>
                </div>
                <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value ?? '—'}</div>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* Content stats */}
      {platform?.content && (
        <>
          <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>Content</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14, marginBottom: 24 }}>
            {[
              { label: 'Resumes',        value: platform.content.total_resumes,      icon: FileText,  color: 'var(--gray-700)' },
              { label: 'Job Posts',      value: platform.content.total_job_posts,    icon: Briefcase, color: 'var(--gray-700)' },
              { label: 'Rankings Run',   value: platform.content.total_rankings,     icon: BarChart2, color: 'var(--gray-700)' },
              { label: 'Training Docs',  value: platform.content.training_pool_size, icon: Database,  color: 'var(--primary)'  },
            ].map((s) => (
              <Card key={s.label} padding="18px">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <s.icon size={18} color={s.color} />
                  <span style={{ fontSize: 12, color: 'var(--gray-500)' }}>{s.label}</span>
                </div>
                <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value ?? '—'}</div>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* Validation stats */}
      {valStats && (
        <>
          <h2 style={{ fontSize: 15, fontWeight: 600, marginBottom: 12 }}>Validation Pipeline</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 24 }}>
            {[
              { label: 'Auto Approve Rate', value: `${valStats.auto_approve_rate}%`, color: 'var(--success)' },
              { label: 'Auto Reject Rate',  value: `${valStats.auto_reject_rate}%`,  color: 'var(--danger)'  },
              { label: 'Pending Review',    value: valStats.pending_admin_review,     color: 'var(--warning)' },
            ].map((s) => (
              <Card key={s.label} padding="18px">
                <div style={{ fontSize: 28, fontWeight: 700, color: s.color }}>{s.value}</div>
                <div style={{ fontSize: 12, color: 'var(--gray-400)', marginTop: 4 }}>{s.label}</div>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* User management */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h2 style={{ fontSize: 15, fontWeight: 600 }}>User Management</h2>
        <select value={userRole} onChange={(e) => setUserRole(e.target.value)} style={selectStyle}>
          <option value="">All roles</option>
          <option value="seeker">Seeker</option>
          <option value="hr">HR</option>
          <option value="admin">Admin</option>
        </select>
      </div>

      <Card padding="0">
        {/* Header */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '2fr 1fr 100px 100px 80px',
          padding: '10px 18px',
          background: 'var(--gray-50)',
          borderBottom: '1px solid var(--gray-200)',
          fontSize: 12, fontWeight: 600, color: 'var(--gray-500)',
        }}>
          <span>User</span>
          <span>Role</span>
          <span>Status</span>
          <span>Joined</span>
          <span>Action</span>
        </div>

        {users.length === 0 ? (
          <p style={{ padding: 24, textAlign: 'center', color: 'var(--gray-400)', fontSize: 13 }}>
            No users found
          </p>
        ) : users.map((u, i) => (
          <div key={u.id} style={{
            display: 'grid',
            gridTemplateColumns: '2fr 1fr 100px 100px 80px',
            padding: '12px 18px',
            borderBottom: i < users.length - 1 ? '1px solid var(--gray-100)' : 'none',
            alignItems: 'center', fontSize: 13,
          }}>
            <div>
              <div style={{ fontWeight: 500 }}>{u.name}</div>
              <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 1 }}>{u.email}</div>
            </div>
            <Badge variant={
              u.role === 'admin' ? 'danger' :
              u.role === 'hr'    ? 'warning' : 'info'
            }>
              {u.role}
            </Badge>
            <Badge variant={u.is_active !== false ? 'success' : 'gray'}>
              {u.is_active !== false ? 'Active' : 'Inactive'}
            </Badge>
            <span style={{ fontSize: 12, color: 'var(--gray-400)' }}>
              {fmtDate(u.created_at)}
            </span>
            {u.role !== 'admin' && (
              <button
                onClick={() => handleDeactivate(u.id, u.is_active !== false)}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer', padding: 4,
                }}
                title={u.is_active !== false ? 'Deactivate' : 'Activate'}
              >
                {u.is_active !== false
                  ? <UserX size={15} color="var(--danger)" />
                  : <UserCheck size={15} color="var(--success)" />
                }
              </button>
            )}
          </div>
        ))}
      </Card>
    </div>
  )
}