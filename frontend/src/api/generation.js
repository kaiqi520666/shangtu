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
