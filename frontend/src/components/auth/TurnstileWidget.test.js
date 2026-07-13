// @vitest-environment jsdom

import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import TurnstileWidget from './TurnstileWidget.vue'

describe('TurnstileWidget', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    delete window.turnstile
    document.querySelectorAll('[data-turnstile-script]').forEach((element) => element.remove())
  })

  it('只加载一次脚本并处理验证、过期和 reset', async () => {
    const options = []
    let nextId = 0
    const turnstile = {
      render: vi.fn((_element, config) => {
        options.push(config)
        return nextId++
      }),
      reset: vi.fn(),
      remove: vi.fn(),
    }
    const append = vi.spyOn(document.head, 'appendChild').mockImplementation((script) => {
      window.turnstile = turnstile
      window.setTimeout(() => script.dispatchEvent(new Event('load')), 0)
      return script
    })
    const props = { siteKey: 'site-key', action: 'login', resetKey: 0 }
    const first = mount(TurnstileWidget, { props })
    await new Promise((resolve) => window.setTimeout(resolve, 0))
    await flushPromises()
    const second = mount(TurnstileWidget, { props })
    await flushPromises()

    expect(append).toHaveBeenCalledOnce()
    expect(turnstile.render).toHaveBeenCalledTimes(2)
    options[0].callback('captcha-token')
    options[0]['expired-callback']()
    expect(first.emitted('verified')[0]).toEqual(['captcha-token'])
    expect(first.emitted('expired')).toHaveLength(1)

    await first.setProps({ resetKey: 1 })
    expect(turnstile.reset).toHaveBeenCalledWith(0)
    first.unmount()
    second.unmount()
    expect(turnstile.remove).toHaveBeenCalledTimes(2)
  })
})
