import request from './request.js'

export function createGenerationJob(scenario) {
  return request.post('/generation/jobs', { scenario }, { timeout: 15000 })
}

export function listGenerationJobs(scenario) {
  return request.get('/generation/jobs', { params: { scenario }, timeout: 15000 })
}

export function getGenerationJob(jobId) {
  return request.get(`/generation/jobs/${jobId}`, { timeout: 15000 })
}

export function updateGenerationJob(jobId, payload) {
  return request.patch(`/generation/jobs/${jobId}`, payload, { timeout: 15000 })
}

export function deleteGenerationJob(jobId) {
  return request.delete(`/generation/jobs/${jobId}`, { timeout: 15000 })
}
