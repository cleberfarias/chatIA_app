/// <reference types="vitest/globals" />

declare global {
  var fetch: typeof globalThis.fetch;
  var localStorage: Storage;
  var ResizeObserver: typeof globalThis.ResizeObserver;
  var IntersectionObserver: typeof globalThis.IntersectionObserver;
  var innerWidth: number;
  var matchMedia: (query: string) => MediaQueryList;
}

export {};