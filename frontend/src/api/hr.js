import api from './axios'

export const hrAPI = {
  // Jobs
  createJob:    (data) => api.post('/hr/jobs', data),
  getJobs:      (params) => api.get('/hr/jobs', { params }),
  getJob:       (id)   => api.get(`/hr/jobs/${id}`),
  updateJob:    (id, data) => api.put(`/hr/jobs/${id}`, data),
  deleteJob:    (id)   => api.delete(`/hr/jobs/${id}`),
  duplicateJob: (id)   => api.post(`/hr/jobs/${id}/duplicate`),

  // CV upload & ranking
  bulkUpload:   (jobId, formData) => api.post(`/hr/bulk-cv-upload/${jobId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  bulkUploadZip: (jobId, formData) => api.post(`/hr/bulk-cv-upload-zip/${jobId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  rankJob:      (jobId, topN, blindMode = false) => api.post(`/hr/job-ranking/${jobId}`, null, {
    params: { top_n: topN, blind_mode: blindMode },
  }),
  getRankings:  (jobId, blindMode = false) => api.get(`/hr/rankings/${jobId}`, {
    params: { blind_mode: blindMode },
  }),

  // Shortlist
  shortlistCandidate: (jobId, data) => api.post(`/hr/shortlist/${jobId}`, data),
  getShortlist:       (jobId, status) => api.get(`/hr/shortlist/${jobId}`, { params: { status } }),
  exportShortlist:    (jobId, format) => api.get(`/hr/shortlist/${jobId}/export`, {
    params: { format },
    responseType: format === 'csv' ? 'blob' : 'json',
  }),

  // Skill gap
  skillGap:     (data) => api.post('/hr/skill-gap', data),

  // Interviews
  scheduleInterview: (data) => api.post('/hr/interviews', data),
  getInterviews:     (params) => api.get('/hr/interviews', { params }),
  getUpcoming:       () => api.get('/hr/interviews/upcoming'),
  updateInterview:   (id, data) => api.put(`/hr/interviews/${id}`, data),

  // Analytics
  getAnalytics: () => api.get('/hr/analytics'),

  // Team & collab
  addTeamMember: (data) => api.post('/hr/team-members', data),
  getTeamMembers: ()    => api.get('/hr/team-members'),
  addComment:    (jobId, data) => api.post(`/hr/comment/${jobId}`, data),
  getComments:   (jobId, candidateId) => api.get(`/hr/comments/${jobId}/${candidateId}`),
  castVote:      (jobId, data) => api.post(`/hr/vote/${jobId}`, data),
}