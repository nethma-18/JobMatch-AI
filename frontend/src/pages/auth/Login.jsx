import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { toast } from 'react-toastify'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import ThemeToggle from '../../components/ui/ThemeToggle'
import { UserCheck } from 'lucide-react'

export default function Login() {
  const { login } = useAuth()
  const navigate  = useNavigate()
  const [form, setForm]       = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)

  const handleChange = (e) =>
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.email || !form.password) {
      toast.error('Please fill in all fields')
      return
    }
    setLoading(true)
    try {
      const user = await login(form.email, form.password)
      toast.success(`Welcome back, ${user.name}!`)
      if (user.role === 'hr')    navigate('/hr')
      else if (user.role === 'admin') navigate('/admin')
      else navigate('/seeker')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      minHeight:      '100vh',
      display:        'flex',
      alignItems:     'center',
      justifyContent: 'center',
      background:     'var(--gray-50)',
      padding:        16,
      transition:     'background-color 0.3s ease',
    }}>
      <div style={{
        width:        '100%',
        maxWidth:     400,
        background:   'var(--card-bg, #fff)',
        borderRadius: 'var(--radius)',
        padding:      36,
        boxShadow:    'var(--shadow-md)',
        border:       '1px solid var(--card-border, var(--gray-200))',
        position:     'relative',
        transition:   'background-color 0.3s ease, border-color 0.3s ease',
      }}>
        {/* Theme Toggle in Top Right */}
        <div style={{ position: 'absolute', top: 16, right: 16 }}>
          <ThemeToggle style={{ padding: '6px', borderRadius: '8px' }} />
        </div>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: 'var(--primary)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: 12,
          }}>
            <UserCheck size={24} color="#fff" />
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>JobMatch AI</h1>
          <p style={{ color: 'var(--gray-500)', marginTop: 4, fontSize: 13 }}>
            Sign in to your account
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Input
            label="Email"
            name="email"
            type="email"
            placeholder="you@example.com"
            value={form.email}
            onChange={handleChange}
            required
          />
          <Input
            label="Password"
            name="password"
            type="password"
            placeholder="••••••••"
            value={form.password}
            onChange={handleChange}
            required
          />
          <Button type="submit" loading={loading} fullWidth style={{ marginTop: 4 }}>
            Sign In
          </Button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'var(--gray-500)' }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--primary)', fontWeight: 500 }}>
            Sign up
          </Link>
        </p>
      </div>
    </div>
  )
}