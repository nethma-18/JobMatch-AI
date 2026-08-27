import api from './axios'

export const seekerAPI = {
  resumeEnhancer:      (data) => api.post('/seeker/resume-enhancer', data),
  atsChecker:          (data) => api.post('/seeker/ats-checker', data),
  rejectionDiagnostic: (data) => api.post('/seeker/rejection-diagnostic', data),
  coverLetter:         (data) => api.post('/seeker/cover-letter', data),
  updateCoverLetter:   (id, data) => api.put(`/seeker/cover-letter/${id}`, data),
  interviewQuestions:  (data) => api.post('/seeker/interview-questions', data),

  // Job tracker
  createApplication:   (data) => api.post('/seeker/applications', data),
  getApplications:     (status) => api.get('/seeker/applications', { params: { status } }),
  getApplication:      (id)  => api.get(`/seeker/applications/${id}`),
  updateApplication:   (id, data) => api.put(`/seeker/applications/${id}`, data),
  deleteApplication:   (id)  => api.delete(`/seeker/applications/${id}`),
  getStats:            ()    => api.get('/seeker/applications-stats'),

  // Profile
  getProfile:          ()    => api.get('/seeker/profile'),
  updateProfile:       (data) => api.put('/seeker/profile', data),
  getJobs:             ()    => api.get('/seeker/jobs'),
}