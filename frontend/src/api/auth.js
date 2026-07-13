import request from './request.js'

export const login = (data) => request.post('/auth/login', data)

export const register = (data) => request.post('/auth/register', data)

export const getCaptchaConfig = () => request.get('/auth/captcha-config')

export const sendRegistrationEmailCode = (data) => request.post('/auth/email-code', data)

export const getCurrentUser = () => request.get('/auth/me')
