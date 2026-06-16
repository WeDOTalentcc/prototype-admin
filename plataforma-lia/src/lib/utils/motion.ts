/**
 * Check if user prefers reduced motion.
 * Use this in JavaScript-driven animations.
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Returns animation duration in ms, respecting reduced motion preference.
 * @param normalDuration - normal duration in ms
 * @param reducedDuration - duration when reduced motion is preferred (default: 0)
 */
export function getAnimationDuration(normalDuration: number, reducedDuration = 0): number {
  return prefersReducedMotion() ? reducedDuration : normalDuration
}
