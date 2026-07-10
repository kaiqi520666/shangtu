import request from "./request.js";

export function getVoiceoverVoices(params = {}) { return request.get("/voiceover/voices", { params, timeout: 15000 }); }
export function getVoiceoverConfig() { return request.get("/voiceover/config", { timeout: 15000 }); }
export function createVoiceoverTask(payload) { return request.post("/voiceover/tasks", payload, { timeout: 15000 }); }
export function getVoiceoverTask(taskId) { return request.get(`/voiceover/tasks/${taskId}`, { timeout: 15000 }); }
export function deleteVoiceoverTask(taskId) { return request.delete(`/voiceover/tasks/${taskId}`, { timeout: 15000 }); }
