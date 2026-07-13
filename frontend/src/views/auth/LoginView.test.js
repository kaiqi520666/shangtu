// @vitest-environment jsdom

import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import LoginView from './LoginView.vue'

const mocks = vi.hoisted(() => ({
  error: vi.fn(),
  getCaptchaConfig: vi.fn(),
  login: vi.fn(),
  loginStore: vi.fn(),
  push: vi.fn(),
  replace: vi.fn(),
  success: vi.fn(),
}))

vi.mock('@/api/auth.js', () => ({
  getCaptchaConfig: mocks.getCaptchaConfig,
  login: mocks.login,
}))
vi.mock('@/stores/auth.js', () => ({ useAuthStore: () => ({ login: mocks.loginStore }) }))
vi.mock('@/composables/useToast.js', () => ({
  useToast: () => ({ success: mocks.success, error: mocks.error }),
}))
vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: mocks.push, replace: mocks.replace }),
}))

describe('LoginView', () => {
  beforeEach(() => vi.clearAllMocks())

  it('按后端信号展示验证码并携带 token 重试登录', async () => {
    mocks.login
      .mockResolvedValueOnce({
        code: 1,
        message: '邮箱或密码错误',
        data: { captcha_required: true },
      })
      .mockResolvedValueOnce({
        code: 0,
        data: { user_id: 1, email: 'user@example.com', token: 'token' },
      })
    mocks.getCaptchaConfig.mockResolvedValue({ code: 0, data: { site_key: 'site-key' } })
    const wrapper = mount(LoginView, {
      global: {
        stubs: {
          AuthPageShell: { template: '<div><slot /></div>' },
          RouterLink: { template: '<a><slot /></a>' },
          TurnstileWidget: {
            emits: ['verified'],
            template: '<button type="button" data-testid="captcha" @click="$emit(\'verified\', \'captcha-token\')">verify</button>',
          },
        },
      },
    })
    await wrapper.find('input[type="email"]').setValue('user@example.com')
    await wrapper.find('input[type="password"]').setValue('wrong-password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(mocks.login).toHaveBeenNthCalledWith(1, {
      email: 'user@example.com',
      password: 'wrong-password',
      captcha_token: undefined,
    })
    expect(mocks.getCaptchaConfig).toHaveBeenCalledOnce()

    await wrapper.get('[data-testid="captcha"]').trigger('click')
    await wrapper.find('input[type="password"]').setValue('correct-password')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(mocks.login).toHaveBeenNthCalledWith(2, {
      email: 'user@example.com',
      password: 'correct-password',
      captcha_token: 'captcha-token',
    })
    expect(mocks.loginStore).toHaveBeenCalledOnce()
    expect(mocks.push).toHaveBeenCalledWith('/generator')
    wrapper.unmount()
  })
})
