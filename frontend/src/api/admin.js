import api from './axios'

export const adminAPI = {
  getPendingReviews: (params) => api.get('/admin/pending-reviews', { params }),
  getReviewDetail:   (id)     => api.get(`/admin/pending-reviews/${id}`),
  approve:           (id, data) => api.post(`/admin/approve/${id}`, data),
  reject:            (id, data) => api.post(`/admin/reject/${id}`, data),

  getTrainingPool:  (params) => api.get('/admin/training-pool', { params }),
  removeFromPool:   (id)     => api.delete(`/admin/training-pool/${id}`),

  retrain:          ()       => api.post('/admin/retrain'),
  getRetrainLogs:   ()       => api.get('/admin/retrain-logs'),

  getValidationStats: ()     => api.get('/admin/validation-stats'),
  getValidationRules: ()     => api.get('/admin/validation-rules'),
  updateValidationRules: (data) => api.put('/admin/validation-rules', data),

  getUsers:         (params) => api.get('/admin/users', { params }),
  deactivateUser:   (id)     => api.put(`/admin/users/${id}/deactivate`),
  activateUser:     (id)     => api.put(`/admin/users/${id}/activate`),

  getPlatformStats: ()       => api.get('/admin/platform-stats'),
}