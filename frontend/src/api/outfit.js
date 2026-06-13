import request from './request.js'

export function listOutfitModels() {
  return request.get('/outfit/models', { timeout: 15000 })
}
