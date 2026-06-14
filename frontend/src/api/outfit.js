import request from './request.js'

export function listOutfitModels() {
  return request.get('/outfit/models', { timeout: 15000 })
}

export function uploadOutfitModel(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/outfit/models/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  })
}

export function deleteOutfitModel(modelId) {
  return request.delete(`/outfit/models/${modelId}`, { timeout: 15000 })
}
