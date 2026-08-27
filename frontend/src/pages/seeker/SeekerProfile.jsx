import { useState, useEffect } from 'react'
import { seekerAPI } from '../../api/seeker'
import { toast } from 'react-toastify'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Input from '../../components/ui/Input'

export default function SeekerProfile() {
  const [profile, setProfile] = useState({
    phone: '',
    location: '',
    professional_title: '',
    summary: '',
    education: '',
    experience: '',
    skills: '',
    certifications: '',
    languages: '',
    linkedin_url: '',
    github_url: '',
    portfolio_url: '',
  })
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    seekerAPI.getProfile()
      .then((res) => {
        setUser(res.data.user)
        const p = res.data.profile || {}
        setProfile({
          phone: p.phone || '',
          location: p.location || '',
          professional_title: p.professional_title || '',
          summary: p.summary || '',
          education: Array.isArray(p.education) ? p.education.join('\n') : (p.education || ''),
          experience: Array.isArray(p.experience) ? p.experience.join('\n') : (p.experience || ''),
          skills: Array.isArray(p.skills) ? p.skills.join(', ') : (p.skills || ''),
          certifications: Array.isArray(p.certifications) ? p.certifications.join(', ') : (p.certifications || ''),
          languages: Array.isArray(p.languages) ? p.languages.join(', ') : (p.languages || ''),
          linkedin_url: p.linkedin_url || '',
          github_url: p.github_url || '',
          portfolio_url: p.portfolio_url || '',
        })
      })
      .catch((err) => {
        toast.error('Failed to load profile')
      })
      .finally(() => setLoading(false))
  }, [])

  const handleChange = (e) => {
    const { name, value } = e.target
    setProfile((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setSaving(true)

    // Convert comma-separated and new-line values back to arrays
    const formattedProfile = {
      ...profile,
      skills: profile.skills.split(',').map(s => s.trim()).filter(Boolean),
      certifications: profile.certifications.split(',').map(c => c.trim()).filter(Boolean),
      languages: profile.languages.split(',').map(l => l.trim()).filter(Boolean),
      education: profile.education.split('\n').map(e => e.trim()).filter(Boolean),
      experience: profile.experience.split('\n').map(exp => exp.trim()).filter(Boolean),
    }

    seekerAPI.updateProfile(formattedProfile)
      .then(() => {
        toast.success('Profile updated successfully')
      })
      .catch((err) => {
        toast.error('Failed to update profile')
      })
      .finally(() => setSaving(false))
  }

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '40px' }}>Loading profile...</div>
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: 700 }}>My Professional Profile</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: '4px' }}>
          Update your professional summary, experience, and contact information.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <Card style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, borderBottom: '1px solid var(--gray-200)', paddingBottom: '8px' }}>
            Basic Information
          </h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <Input
              label="Full Name"
              value={user?.name || ''}
              disabled
            />
            <Input
              label="Email Address"
              value={user?.email || ''}
              disabled
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <Input
              label="Phone Number"
              name="phone"
              placeholder="+1 (555) 123-4567"
              value={profile.phone}
              onChange={handleChange}
            />
            <Input
              label="Location"
              name="location"
              placeholder="San Francisco, CA"
              value={profile.location}
              onChange={handleChange}
            />
          </div>

          <Input
            label="Professional Title"
            name="professional_title"
            placeholder="Software Engineer / Product Manager"
            value={profile.professional_title}
            onChange={handleChange}
          />

          <Input
            label="Professional Summary"
            name="summary"
            placeholder="Tell us about yourself..."
            rows={4}
            value={profile.summary}
            onChange={handleChange}
          />
        </Card>

        <Card style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, borderBottom: '1px solid var(--gray-200)', paddingBottom: '8px' }}>
            Experience & Education
          </h2>

          <Input
            label="Experience (One entry per line)"
            name="experience"
            placeholder="Senior Developer at Google (2022-Present)&#10;Software Engineer at Stripe (2020-2022)"
            rows={4}
            value={profile.experience}
            onChange={handleChange}
          />

          <Input
            label="Education (One entry per line)"
            name="education"
            placeholder="B.S. Computer Science at Stanford University (2016-2020)"
            rows={4}
            value={profile.education}
            onChange={handleChange}
          />
        </Card>

        <Card style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, borderBottom: '1px solid var(--gray-200)', paddingBottom: '8px' }}>
            Skills, Certifications & Languages
          </h2>

          <Input
            label="Skills (Comma-separated)"
            name="skills"
            placeholder="React, Node.js, Python, MongoDB"
            value={profile.skills}
            onChange={handleChange}
          />

          <Input
            label="Certifications (Comma-separated)"
            name="certifications"
            placeholder="AWS Solutions Architect, PMP"
            value={profile.certifications}
            onChange={handleChange}
          />

          <Input
            label="Languages (Comma-separated)"
            name="languages"
            placeholder="English (Fluent), Spanish (Intermediate)"
            value={profile.languages}
            onChange={handleChange}
          />
        </Card>

        <Card style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '24px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: 600, borderBottom: '1px solid var(--gray-200)', paddingBottom: '8px' }}>
            Social Links
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <Input
              label="LinkedIn URL"
              name="linkedin_url"
              placeholder="https://linkedin.com/in/username"
              value={profile.linkedin_url}
              onChange={handleChange}
            />
            <Input
              label="GitHub URL"
              name="github_url"
              placeholder="https://github.com/username"
              value={profile.github_url}
              onChange={handleChange}
            />
          </div>

          <Input
            label="Portfolio URL"
            name="portfolio_url"
            placeholder="https://portfolio.com"
            value={profile.portfolio_url}
            onChange={handleChange}
          />
        </Card>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginBottom: '40px' }}>
          <Button type="submit" disabled={saving}>
            {saving ? 'Saving...' : 'Save Profile'}
          </Button>
        </div>
      </form>
    </div>
  )
}
