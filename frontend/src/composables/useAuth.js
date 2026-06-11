import { computed, ref } from 'vue'

const STORAGE_KEY = 'nodepass_auth_user'
const user = ref(readUser())

export function useAuth() {
  const isLoggedIn = computed(() => Boolean(user.value?.email))

  function login(payload) {
    user.value = {
      email: payload.email,
      username: payload.username || payload.email?.split('@')[0],
      token: payload.token,
      userId: payload.userId,
      plan: 'SaaS Pro',
    }
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(user.value))
  }

  function logout() {
    user.value = null
    window.localStorage.removeItem(STORAGE_KEY)
  }

  return {
    user,
    isLoggedIn,
    login,
    logout,
    getToken: () => user.value?.token || '',
  }
}

function readUser() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}
