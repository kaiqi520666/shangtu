import request from './request.js'

export function uploadImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/image/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
}

export function analyzeImage({ image_url, platform = '', language = '中文' }) {
  return request.post(
    '/image/analyze',
    { image_url, platform, language },
    { timeout: 120000 },
  )
}

export function generateImage({
  prompt,
  image_url = null,
  ratio,
  resolution,
  job_id = null,
  type_id = null,
  title = null,
  sort_order = 0,
}) {
  return request.post(
    '/image/generate',
    { prompt, image_url, ratio, resolution, job_id, type_id, title, sort_order },
    { timeout: 60000 },
  )
}

export function getImageTask(taskId) {
  return request.get(`/image/task/${taskId}`, { timeout: 15000 })
}
