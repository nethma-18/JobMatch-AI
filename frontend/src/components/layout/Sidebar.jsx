import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import ThemeToggle from '../ui/ThemeToggle'
import {
  LayoutDashboard, FileText, CheckSquare, AlertCircle,
  Mail, MessageSquare, Briefcase, Users, BarChart2,
  Calendar, UserCheck, Settings, LogOut, Shield,
  Upload, List, Star, TrendingUp, Database, User,
} from 'lucide-react'

const seekerLinks = [
  { to: '/seeker',              icon: LayoutDashboard, label: 'Dashboard'         },
  { to: '/seeker/profile',      icon: User,            label: 'Profile'           },
  { to: '/seeker/resumes',      icon: FileText,        label: 'Resumes'           },
  { to: '/seeker/enhancer',     icon: TrendingUp,      label: 'Resume Enhancer'   },
  { to: '/seeker/ats',          icon: CheckSquare,     label: 'ATS Checker'       },
  { to: '/seeker/diagnostic',   icon: AlertCircle,     label: 'Rejection Diagnostic'},
  { to: '/seeker/cover-letter', icon: Mail,            label: 'Cover Letter'      },
  { to: '/seeker/interview-q',  icon: MessageSquare,   label: 'Interview Q&A'     },
  { to: '/seeker/tracker',      icon: Briefcase,       label: 'Job Tracker'       },
]

const hrLinks = [
  { to: '/hr',             icon: LayoutDashboard, label: 'Dashboard'      },
  { to: '/hr/jobs',        icon: Briefcase,       label: 'Job Posts'      },
  { to: '/hr/upload',      icon: Upload,          label: 'Bulk Upload'    },
  { to: '/hr/ranking',     icon: List,            label: 'Job Ranking'    },
  { to: '/hr/shortlist',   icon: Star,            label: 'Shortlist'      },
  { to: '/hr/skill-gap',   icon: TrendingUp,      label: 'Skill Gap'      },
  { to: '/hr/interviews',  icon: Calendar,        label: 'Interviews'     },
  { to: '/hr/analytics',   icon: BarChart2,       label: 'Analytics'      },
  { to: '/hr/collab',      icon: Users,           label: 'Team & Collab'  },
]

const adminLinks = [
  { to: '/admin',           icon: LayoutDashboard, label: 'Dashboard'      },
  { to: '/admin/queue',     icon: CheckSquare,     label: 'Review Queue'   },
  { to: '/admin/pool',      icon: Database,        label: 'Training Pool'  },
  { to: '/admin/stats',     icon: BarChart2,       label: 'Platform Stats' },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const links =
    user?.role === 'hr'    ? hrLinks :
    user?.role === 'admin' ? adminLinks :
    seekerLinks

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const linkStyle = (isActive) => ({
    display:        'flex',
    alignItems:     'center',
    gap:            12,
    padding:        '10px 14px',
    borderRadius:   'var(--radius-sm, 8px)',
    fontSize:       13,
    fontWeight:     isActive ? 600 : 500,
    color:          isActive ? 'var(--gray-900)' : 'var(--gray-500)',
    background:     isActive ? 'var(--primary-light)' : 'transparent',
    borderLeft:     isActive ? '3px solid var(--primary)' : '3px solid transparent',
    transition:     'all 0.18s cubic-bezier(0.4, 0, 0.2, 1)',
    textDecoration: 'none',
    boxShadow:      isActive ? 'var(--shadow-glow)' : 'none',
  })

  return (
    <aside style={{
      width:      'var(--sidebar-w)',
      minHeight:  '100vh',
      background: 'var(--sidebar-bg, #fff)',
      borderRight: '1px solid var(--card-border, var(--gray-200))',
      display:    'flex',
      flexDirection: 'column',
      position:   'fixed',
      top:        0,
      left:       0,
      zIndex:     100,
      transition: 'background-color 0.3s ease, border-color 0.3s ease',
    }}>
      {/* Logo + Theme Toggle */}
      <div style={{
        padding:     '16px 14px',
        borderBottom: '1px solid var(--card-border, var(--gray-200))',
        display:     'flex',
        alignItems:  'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'var(--primary)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}>
            <UserCheck size={18} color="#fff" />
          </div>
          <div>
            <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--gray-900)' }}>
              JobMatch AI
            </div>
            <div style={{ fontSize: 10, color: 'var(--gray-400)', textTransform: 'capitalize' }}>
              {user?.role} portal
            </div>
          </div>
        </div>

        <ThemeToggle style={{ padding: '6px', borderRadius: '8px' }} />
      </div>

      {/* Nav links */}
      <nav style={{ flex: 1, padding: '12px 10px', overflowY: 'auto' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {links.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to.split('/').length <= 2}
              style={({ isActive }) => linkStyle(isActive)}
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* User + logout */}
      <div style={{
        padding:   '12px 10px',
        borderTop: '1px solid var(--card-border, var(--gray-200))',
      }}>
        <div style={{
          padding:      '8px 10px',
          borderRadius: 8,
          marginBottom: 4,
        }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--gray-800)' }}>
            {user?.name}
          </div>
          <div style={{ fontSize: 11, color: 'var(--gray-400)', marginTop: 1 }}>
            {user?.email}
          </div>
        </div>
        <button
          onClick={handleLogout}
          style={{
            display:      'flex',
            alignItems:   'center',
            gap:          8,
            width:        '100%',
            padding:      '8px 10px',
            background:   'none',
            border:       'none',
            borderRadius: 8,
            cursor:       'pointer',
            color:        'var(--danger)',
            fontSize:     13,
          }}
        >
          <LogOut size={15} />
          Log out
        </button>
      </div>
    </aside>
  )
}