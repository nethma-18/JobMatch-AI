import api from './axios'

export const sharedAPI = {
  // Uploads
  uploadResume:         (formData) => api.post('/upload/resume', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  uploadJobDescription: (formData) => api.post('/upload/job-description', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getMyResumes:         ()             => api.get('/my-resumes'),
  getResume:            (id)           => api.get(`/resumes/${id}`),
  deleteResume:         (id)           => api.delete(`/resumes/${id}`),

  // Notifications
  getNotifications:     ()             => api.get('/notifications'),
  markRead:             (id)           => api.put(`/notifications/${id}/read`),
  markAllRead:          ()             => api.put('/notifications/read-all'),
}