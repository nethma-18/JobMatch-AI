import { useState, useEffect } from 'react'
import { hrAPI } from '../../api/hr'
import Card from '../../components/ui/Card'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  FunnelChart, Funnel, LabelList, PieChart, Pie, Cell, Legend,
} from 'recharts'
import { BarChart2, TrendingUp } from 'lucide-react'

const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#3b82f6']

export default function Analytics() {
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    hrAPI.getAnalytics()
      .then((r) => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p style={{ padding: 40, color: 'var(--gray-400)', textAlign: 'center' }}>Loading analytics...</p>
  if (!data)   return <p style={{ padding: 40, color: 'var(--gray-400)', textAlign: 'center' }}>No data available</p>

  const ov = data.overview || {}

  const overviewCards = [
    { label: 'Total Jobs',        value: ov.total_jobs          || 0, color: 'var(--primary)' },
    { label: 'Open Jobs',         value: ov.open_jobs           || 0, color: 'var(--success)' },
    { label: 'CVs Processed',     value: ov.total_cv_processed  || 0, color: 'var(--info)'    },
    { label: 'Avg Match Score',   value: `${ov.average_match_score || 0}%`, color: 'var(--warning)' },
    { label: 'Shortlisted',       value: ov.total_shortlisted   || 0, color: 'var(--success)' },
    { label: 'Interviews',        value: ov.total_interviews     || 0, color: 'var(--purple)'  },
  ]

  // Score distribution
  const scoreDistData = (data.score_distribution?.labels || []).map((l, i) => ({
    range: l, count: (data.score_distribution?.data || [])[i] || 0,
  }))

  // Funnel data
  const funnelData = (data.hiring_funnel?.stages || []).map((s, i) => ({
    name:  s,
    value: (data.hiring_funnel?.counts || [])[i] || 0,
    fill:  COLORS[i % COLORS.length],
  }))

  // Apps by job
  const appsByJob = data.applications_by_job || []

  // Top skills
  const topSkills = data.top_skills_demanded || []

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700 }}>HR Analytics</h1>
        <p style={{ color: 'var(--gray-500)', marginTop: 4 }}>Hiring metrics and pipeline insights</p>
      </div>

      {/* Overview */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginBottom: 24 }}>
        {overviewCards.map((s) => (
          <Card key={s.label} padding="18px">
            <div style={{ fontSize: 26, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 13, color: 'var(--gray-500)', marginTop: 4 }}>{s.label}</div>
          </Card>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginBottom: 20 }}>
        {/* Score distribution */}
        <Card>
          <h3 style={{ fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <BarChart2 size={18} color="var(--primary)" /> Match Score Distribution
          </h3>
          {scoreDistData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={scoreDistData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <XAxis dataKey="range" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Bar dataKey="count" fill="var(--primary)" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ color: 'var(--gray-400)', textAlign: 'center', padding: 40, fontSize: 13 }}>
              No ranking data yet
            </p>
          )}
        </Card>

        {/* CVs per job */}
        <Card>
          <h3 style={{ fontWeight: 600, marginBottom: 16 }}>CVs Received per Job</h3>
          {appsByJob.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={appsByJob} layout="vertical" margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <XAxis type="number" fontSize={12} />
                <YAxis
                  type="category" dataKey="job_title" fontSize={11}
                  width={100}
                  tickFormatter={(v) => v.length > 14 ? v.slice(0, 14) + '...' : v}
                />
                <Tooltip />
                <Bar dataKey="cv_count" fill="var(--info)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ color: 'var(--gray-400)', textAlign: 'center', padding: 40, fontSize: 13 }}>
              No data yet
            </p>
          )}
        </Card>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
        {/* Hiring funnel */}
        <Card>
          <h3 style={{ fontWeight: 600, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <TrendingUp size={18} color="var(--success)" /> Hiring Funnel
          </h3>
          {funnelData.length > 0 ? (
            <div>
              {funnelData.map((stage, i) => (
                <div key={stage.name} style={{ marginBottom: 12 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 13, color: 'var(--gray-600)' }}>{stage.name}</span>
                    <span style={{ fontSize: 13, fontWeight: 600 }}>{stage.value}</span>
                  </div>
                  <div style={{ height: 28, background: 'var(--gray-100)', borderRadius: 6, overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: funnelData[0].value > 0
                        ? `${(stage.value / funnelData[0].value) * 100}%` : '0%',
                      background: stage.fill,
                      borderRadius: 6,
                      transition: 'width 0.6s ease',
                      display: 'flex', alignItems: 'center', paddingLeft: 8,
                    }}>
                      {stage.value > 0 && (
                        <span style={{ fontSize: 11, color: '#fff', fontWeight: 600 }}>
                          {funnelData[0].value > 0
                            ? `${Math.round((stage.value / funnelData[0].value) * 100)}%`
                            : '0%'}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--gray-400)', textAlign: 'center', padding: 40, fontSize: 13 }}>
              No funnel data yet
            </p>
          )}
        </Card>

        {/* Top skills demanded */}
        <Card>
          <h3 style={{ fontWeight: 600, marginBottom: 16 }}>Top Skills Demanded</h3>
          {topSkills.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {topSkills.slice(0, 8).map((s, i) => (
                <div key={s.skill}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                    <span style={{ fontSize: 13, textTransform: 'capitalize' }}>{s.skill}</span>
                    <span style={{ fontSize: 12, color: 'var(--gray-400)' }}>{s.count} jobs</span>
                  </div>
                  <div style={{ height: 6, background: 'var(--gray-100)', borderRadius: 999, overflow: 'hidden' }}>
                    <div style={{
                      height: '100%',
                      width: `${(s.count / topSkills[0].count) * 100}%`,
                      background: COLORS[i % COLORS.length],
                      borderRadius: 999,
                    }} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: 'var(--gray-400)', textAlign: 'center', padding: 40, fontSize: 13 }}>
              Create job posts with required skills to see data
            </p>
          )}
        </Card>
      </div>
    </div>
  )
}