import '@testing-library/jest-dom'
import { vi } from 'vitest'

// jsdom não implementa Element.prototype.scrollIntoView. Vários componentes
// (StudioTour/TourSpotlight, onboarding, chat) chamam scrollIntoView dentro de
// effects no mount — sem este polyfill o render derruba o teste com
// "el.scrollIntoView is not a function". Polyfill global cobre o gap conhecido
// do jsdom para toda a suíte que usa este setup.
if (typeof Element !== 'undefined' && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = vi.fn()
}
