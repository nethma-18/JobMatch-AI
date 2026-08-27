import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { toast } from 'react-toastify'
import Input from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import ThemeToggle from '../../components/ui/ThemeToggle'
import { UserCheck } from 'lucide-react'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    name: '', email: '', password: '',
    role: 'seeker', company_name: '',
  })
  const [loading, setLoading] = useState(false)

  const handleChange = (e) =>
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.name || !form.email || !form.password) {
      toast.error('Please fill in all required fields')
      return
    }
    if (form.role === 'hr' && !form.company_name) {
      toast.error('Company name is required for HR accounts')
      return
    }
    setLoading(true)
    try {
      const user = await register(form)
      toast.success(`Account created! Welcome, ${user.name}`)
      if (user.role === 'hr') navigate('/hr')
      else navigate('/seeker')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  const selectStyle = {
    width: '100%', padding: '9px 12px',
    border: '1px solid var(--gray-300)',
    borderRadius: 'var(--radius)', fontSize: 14,
    background: 'var(--input-bg, #fff)', color: 'var(--gray-800)',
    cursor: 'pointer',
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex',
      alignItems: 'center', justifyContent: 'center',
      background: 'var(--gray-50)', padding: 16,
      transition: 'background-color 0.3s ease',
    }}>
      <div style={{
        width: '100%', maxWidth: 420,
        background: 'var(--card-bg, #fff)', borderRadius: 'var(--radius)',
        padding: 36, boxShadow: 'var(--shadow-md)',
        border: '1px solid var(--card-border, var(--gray-200))',
        position: 'relative',
        transition: 'background-color 0.3s ease, border-color 0.3s ease',
      }}>
        {/* Theme Toggle in Top Right */}
        <div style={{ position: 'absolute', top: 16, right: 16 }}>
          <ThemeToggle style={{ padding: '6px', borderRadius: '8px' }} />
        </div>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: 'var(--primary)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: 12,
          }}>
            <UserCheck size={24} color="#fff" />
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>Create Account</h1>
          <p style={{ color: 'var(--gray-500)', marginTop: 4, fontSize: 13 }}>
            Join JobMatch AI today
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <Input
            label="Full Name" name="name" placeholder="John Smith"
            value={form.name} onChange={handleChange} required
          />
          <Input
            label="Email" name="email" type="email" placeholder="you@example.com"
            value={form.email} onChange={handleChange} required
          />
          <Input
            label="Password" name="password" type="password" placeholder="Min 6 characters"
            value={form.password} onChange={handleChange} required
          />

          {/* Role selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 13, fontWeight: 500, color: 'var(--gray-700)' }}>
              I am a <span style={{ color: 'var(--danger)' }}>*</span>
            </label>
            <select name="role" value={form.role} onChange={handleChange} style={selectStyle}>
              <option value="seeker">Job Seeker</option>
              <option value="hr">HR Recruiter</option>
            </select>
          </div>

          {form.role === 'hr' && (
            <Input
              label="Company Name" name="company_name" placeholder="Acme Corp"
              value={form.company_name} onChange={handleChange} required
            />
          )}

          <Button type="submit" loading={loading} fullWidth style={{ marginTop: 4 }}>
            Create Account
          </Button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 20, fontSize: 13, color: 'var(--gray-500)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--primary)', fontWeight: 500 }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}