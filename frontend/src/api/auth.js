import request from './request.js'

export const login = (data) => request.post('/auth/login', data)

export const register = (data) => request.post('/auth/register', data)

export const sendRegistrationEmailCode = (email) => request.post('/auth/email-code', { email })

export const getCurrentUser = () => request.get('/auth/me')
