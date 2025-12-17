import { config } from '@vue/test-utils'
import { vi } from 'vitest'

// Mock global objects
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn()
}))

// Mock CSS imports
vi.mock('*.css', () => ({}))
vi.mock('*.scss', () => ({}))

// Configure Vue Test Utils
config.global.stubs = {
  transition: false,
  'transition-group': false,
  'v-icon': true,
  'v-card': true,
  'v-card-text': true
}
