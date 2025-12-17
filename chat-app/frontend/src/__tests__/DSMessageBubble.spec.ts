import { describe, it, expect } from 'vitest'

describe('Vitest Setup', () => {
  it('soma dois números', () => {
    expect(1 + 1).toBe(2)
  })

  it('verifica tipos', () => {
    const msg = 'Hello World'
    expect(typeof msg).toBe('string')
  })

  it('trabalha com arrays', () => {
    const arr = [1, 2, 3]
    expect(arr).toHaveLength(3)
    expect(arr).toContain(2)
  })
})
