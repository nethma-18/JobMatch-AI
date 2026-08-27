import api from './axios'

export const authAPI = {
  register: (data)         => api.post('/auth/register', data),
  login:    (data)         => api.post('/auth/login', data),
  getMe:    ()             => api.get('/auth/me'),
  updateMe: (data)         => api.put('/auth/me', data),
  changePassword: (data)   => api.put('/auth/change-password', data),
  logout:   ()             => api.post('/auth/logout'),
}