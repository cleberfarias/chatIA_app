/**
 * 📱 Breakpoints Responsivos (Mobile First)
 * 
 * Segue o padrão do Vuetify e boas práticas de design responsivo
 * Prioridade: Mobile → Tablet → Desktop
 */

export const breakpoints = {
  // Valores em pixels
  xs: 0,      // 📱 Extra small (mobile portrait)
  sm: 600,    // 📱 Small (mobile landscape)
  md: 960,    // 📱 Medium (tablet portrait)
  lg: 1264,   // 💻 Large (tablet landscape / small desktop)
  xl: 1904,   // 🖥️ Extra large (desktop)
} as const;

/**
 * Media queries para uso em componentes
 * 
 * @example
 * ```css
 * .component {
 *   width: 100%;
 * }
 * 
 * @media (min-width: 960px) {
 *   .component {
 *     width: 80%;
 *   }
 * }
 * ```
 */
export const mediaQueries = {
  // Mobile first - min-width
  xs: `@media (min-width: ${breakpoints.xs}px)`,
  sm: `@media (min-width: ${breakpoints.sm}px)`,
  md: `@media (min-width: ${breakpoints.md}px)`,
  lg: `@media (min-width: ${breakpoints.lg}px)`,
  xl: `@media (min-width: ${breakpoints.xl}px)`,
  
  // Max-width (para casos específicos)
  maxXs: `@media (max-width: ${breakpoints.sm - 1}px)`,
  maxSm: `@media (max-width: ${breakpoints.md - 1}px)`,
  maxMd: `@media (max-width: ${breakpoints.lg - 1}px)`,
  maxLg: `@media (max-width: ${breakpoints.xl - 1}px)`,
  
  // Entre breakpoints
  onlyXs: `@media (max-width: ${breakpoints.sm - 1}px)`,
  onlySm: `@media (min-width: ${breakpoints.sm}px) and (max-width: ${breakpoints.md - 1}px)`,
  onlyMd: `@media (min-width: ${breakpoints.md}px) and (max-width: ${breakpoints.lg - 1}px)`,
  onlyLg: `@media (min-width: ${breakpoints.lg}px) and (max-width: ${breakpoints.xl - 1}px)`,
  onlyXl: `@media (min-width: ${breakpoints.xl}px)`,
  
  // Orientação
  portrait: '@media (orientation: portrait)',
  landscape: '@media (orientation: landscape)',
  
  // Touch devices
  touch: '@media (hover: none) and (pointer: coarse)',
  mouse: '@media (hover: hover) and (pointer: fine)',
} as const;

/**
 * Composable para uso em scripts Vue
 * 
 * @example
 * ```typescript
 * import { useBreakpoint } from '@/design-system/tokens/breakpoints';
 * 
 * const { isMobile, isTablet, isDesktop } = useBreakpoint();
 * ```
 */
export function useBreakpoint() {
  const isMobile = window.matchMedia(`(max-width: ${breakpoints.md - 1}px)`).matches;
  const isTablet = window.matchMedia(
    `(min-width: ${breakpoints.md}px) and (max-width: ${breakpoints.lg - 1}px)`
  ).matches;
  const isDesktop = window.matchMedia(`(min-width: ${breakpoints.lg}px)`).matches;
  const isMobilePortrait = window.matchMedia('(max-width: 599px) and (orientation: portrait)').matches;
  const isMobileLandscape = window.matchMedia(
    '(min-width: 600px) and (max-width: 959px) and (orientation: landscape)'
  ).matches;
  
  return {
    isMobile,
    isTablet,
    isDesktop,
    isMobilePortrait,
    isMobileLandscape,
    isTouch: window.matchMedia('(hover: none) and (pointer: coarse)').matches,
  };
}

/**
 * Helper para valores responsivos
 * 
 * @example
 * ```typescript
 * const padding = responsive({
 *   xs: '8px',
 *   md: '16px',
 *   lg: '24px'
 * });
 * ```
 */
export function responsive<T>(values: Partial<Record<keyof typeof breakpoints, T>>): T {
  const { isMobile, isTablet, isDesktop } = useBreakpoint();
  
  if (isDesktop && values.xl) return values.xl;
  if (isDesktop && values.lg) return values.lg;
  if (isTablet && values.md) return values.md;
  if (isMobile && values.sm) return values.sm;
  if (values.xs) return values.xs;
  
  // Fallback para o primeiro valor disponível
  return Object.values(values)[0] as T;
}
