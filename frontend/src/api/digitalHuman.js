import request from "./request.js";

export function getDigitalHumanAvatars(params = {}) {
  return request.get("/digital-human/avatars", { params, timeout: 15000 });
}

export function getDigitalHumanVoices(params = {}) {
  return request.get("/digital-human/voices", { params, timeout: 15000 });
}
