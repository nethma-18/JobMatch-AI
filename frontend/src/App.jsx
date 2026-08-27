import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import ProtectedRoute from './components/guards/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'

// Auth pages
import Login    from './pages/auth/Login'
import Register from './pages/auth/Register'

// Seeker pages
import SeekerDashboard    from './pages/seeker/SeekerDashboard'
import ResumeEnhancer     from './pages/seeker/ResumeEnhancer'
import ATSChecker         from './pages/seeker/ATSChecker'
import RejectionDiagnostic from './pages/seeker/RejectionDiagnostic'
import CoverLetter        from './pages/seeker/CoverLetter'
import InterviewQuestions from './pages/seeker/InterviewQuestions'
import JobTracker         from './pages/seeker/JobTracker'
import SeekerProfile      from './pages/seeker/SeekerProfile'
import ResumeManager      from './pages/seeker/ResumeManager'

// HR pages
import HRDashboard  from './pages/hr/HRDashboard'
import JobPosts     from './pages/hr/JobPosts'
import BulkUpload   from './pages/hr/BulkUpload'
import JobRanking   from './pages/hr/JobRanking'
import Shortlist    from './pages/hr/Shortlist'
import SkillGap     from './pages/hr/SkillGap'
import Interviews   from './pages/hr/Interviews'
import Analytics    from './pages/hr/Analytics'
import CollabHiring from './pages/hr/CollabHiring'

// Admin pages
import AdminDashboard  from './pages/admin/AdminDashboard'
import ValidationQueue from './pages/admin/ValidationQueue'
import TrainingPool    from './pages/admin/TrainingPool'
import PlatformStats   from './pages/admin/PlatformStats'

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
        <Routes>
          {/* Public */}
          <Route path="/login"    element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/"         element={<Navigate to="/login" replace />} />

          {/* Seeker */}
          <Route element={
            <ProtectedRoute roles={['seeker']}>
              <AppLayout />
            </ProtectedRoute>
          }>
            <Route path="/seeker"              element={<SeekerDashboard />} />
            <Route path="/seeker/profile"      element={<SeekerProfile />} />
            <Route path="/seeker/resumes"      element={<ResumeManager />} />
            <Route path="/seeker/enhancer"     element={<ResumeEnhancer />} />
            <Route path="/seeker/ats"          element={<ATSChecker />} />
            <Route path="/seeker/diagnostic"   element={<RejectionDiagnostic />} />
            <Route path="/seeker/cover-letter" element={<CoverLetter />} />
            <Route path="/seeker/interview-q"  element={<InterviewQuestions />} />
            <Route path="/seeker/tracker"      element={<JobTracker />} />
          </Route>

          {/* HR */}
          <Route element={
            <ProtectedRoute roles={['hr']}>
              <AppLayout />
            </ProtectedRoute>
          }>
            <Route path="/hr"             element={<HRDashboard />} />
            <Route path="/hr/jobs"        element={<JobPosts />} />
            <Route path="/hr/upload"      element={<BulkUpload />} />
            <Route path="/hr/ranking"     element={<JobRanking />} />
            <Route path="/hr/shortlist"   element={<Shortlist />} />
            <Route path="/hr/skill-gap"   element={<SkillGap />} />
            <Route path="/hr/interviews"  element={<Interviews />} />
            <Route path="/hr/analytics"   element={<Analytics />} />
            <Route path="/hr/collab"      element={<CollabHiring />} />
          </Route>

          {/* Admin */}
          <Route element={
            <ProtectedRoute roles={['admin']}>
              <AppLayout />
            </ProtectedRoute>
          }>
            <Route path="/admin"        element={<AdminDashboard />} />
            <Route path="/admin/queue"  element={<ValidationQueue />} />
            <Route path="/admin/pool"   element={<TrainingPool />} />
            <Route path="/admin/stats"  element={<PlatformStats />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  </ThemeProvider>
  )
}