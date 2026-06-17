# Utility Classes Reference - Design System LIA v4.1

```css
/* ============ BUTTONS ============ */
.btn {
  @apply px-4 py-2 rounded text-sm font-semibold transition-all duration-150 focus:outline-none;
}
.btn-primary {
  @apply btn bg-gray-900 text-white hover:bg-gray-800 focus:ring-2 focus:ring-gray-900/20;
}
.btn-secondary {
  @apply btn bg-transparent text-gray-900 border border-gray-300 hover:bg-gray-50;
}

/* ============ CARDS ============ */
.card {
  @apply bg-white border border-gray-200 rounded-md shadow-sm p-6;
}
.card-interactive {
  @apply card transition-all duration-150 hover:shadow-md hover:-translate-y-0.5 cursor-pointer;
}

/* ============ INPUTS ============ */
.input {
  @apply w-full px-3 py-2 text-sm text-gray-900 bg-white border border-gray-300 rounded 
         focus:border-gray-900 focus:ring-2 focus:ring-gray-900/20 focus:outline-none;
}
.input-error {
  @apply input border-red-500 focus:ring-red-500/20;
}

/* ============ BADGES ============ */
.badge {
  @apply inline-flex items-center px-2 py-1 rounded text-xs font-medium border;
}
.badge-success {
  @apply badge bg-green-50 text-green-700 border-green-200;
}
.badge-warning {
  @apply badge bg-amber-50 text-amber-700 border-amber-200;
}
.badge-error {
  @apply badge bg-red-50 text-red-700 border-red-200;
}
```
