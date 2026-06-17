# Navigation & Loading Reference - Design System LIA v4.1

## Sidebar Navigation
```html
<nav class="w-64 h-screen bg-white border-r border-gray-200 p-4">
  <div class="mb-6">
    <div class="flex items-center gap-2 px-3 py-2">
      <svg class="w-6 h-6 text-[#60BED1]"><!-- Brain Icon --></svg>
      <span class="text-lg font-bold text-gray-900 font-['Open_Sans']">LIA</span>
    </div>
  </div>
  <div class="space-y-1">
    <!-- Active -->
    <a href="#" class="flex items-center gap-3 px-3 py-2 bg-gray-100 text-gray-900 rounded-md font-semibold text-sm">
      <svg class="w-5 h-5">...</svg><span>Dashboard</span>
    </a>
    <!-- Inactive -->
    <a href="#" class="flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-50 hover:text-gray-900 rounded-md text-sm">
      <svg class="w-5 h-5">...</svg><span>Vagas</span>
    </a>
  </div>
</nav>

<!-- Vuetify -->
<v-navigation-drawer permanent width="256">
  <v-list>
    <v-list-item v-for="item in items" :key="item.title"
      :prepend-icon="item.icon" :title="item.title" :active="item.active" color="grey-darken-4">
    </v-list-item>
  </v-list>
</v-navigation-drawer>
```

## Top Navigation
```html
<header class="h-16 bg-white border-b border-gray-200 px-6 flex items-center justify-between">
  <div class="flex items-center gap-6">
    <div class="flex items-center gap-2">
      <svg class="w-6 h-6 text-[#60BED1]">...</svg>
      <span class="text-lg font-bold text-gray-900">LIA</span>
    </div>
    <nav class="flex items-center gap-1">
      <a href="#" class="px-3 py-2 text-sm font-semibold text-gray-900 border-b-2 border-gray-900">Dashboard</a>
      <a href="#" class="px-3 py-2 text-sm text-gray-600 hover:text-gray-900">Vagas</a>
    </nav>
  </div>
  <div class="flex items-center gap-3">
    <button class="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded"><svg class="w-5 h-5">...</svg></button>
    <div class="w-8 h-8 bg-gray-200 rounded-full"></div>
  </div>
</header>

<!-- Vuetify -->
<v-app-bar color="white" elevation="1">
  <v-app-bar-title>LIA</v-app-bar-title>
  <v-tabs class="ml-6"><v-tab>Dashboard</v-tab><v-tab>Vagas</v-tab></v-tabs>
  <template #append>
    <v-btn icon="mdi-bell" variant="text"></v-btn>
    <v-avatar size="32" color="grey-lighten-2"></v-avatar>
  </template>
</v-app-bar>
```

## Breadcrumbs
```html
<nav class="flex items-center gap-2 text-sm">
  <a href="#" class="text-gray-600 hover:text-gray-900">Home</a>
  <svg class="w-4 h-4 text-gray-400">...</svg>
  <a href="#" class="text-gray-600 hover:text-gray-900">Vagas</a>
  <svg class="w-4 h-4 text-gray-400">...</svg>
  <span class="text-gray-900 font-semibold">Desenvolvedor</span>
</nav>
<v-breadcrumbs :items="['Home', 'Vagas', 'Desenvolvedor']"></v-breadcrumbs>
```

---

## Loading - Spinner
```html
<div class="flex items-center justify-center p-12">
  <svg class="w-8 h-8 animate-spin text-gray-900" viewBox="0 0 24 24">
    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
  </svg>
</div>
<v-progress-circular indeterminate color="grey-darken-4"></v-progress-circular>
```

## Loading - Progress Bar
```html
<div class="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
  <div class="bg-gray-900 h-2 rounded-full transition-all duration-300" style="width: 65%"></div>
</div>
<v-progress-linear :model-value="65" color="grey-darken-4"></v-progress-linear>
```

## Loading - Skeleton
```html
<div class="animate-pulse space-y-4">
  <div class="h-6 bg-gray-200 rounded w-1/3"></div>
  <div class="space-y-2">
    <div class="h-4 bg-gray-200 rounded"></div>
    <div class="h-4 bg-gray-200 rounded w-5/6"></div>
    <div class="h-4 bg-gray-200 rounded w-4/6"></div>
  </div>
</div>
<v-skeleton-loader type="article"></v-skeleton-loader>

<!-- Card skeleton -->
<div class="bg-white rounded-md border border-gray-200 p-6 animate-pulse">
  <div class="flex items-center gap-3 mb-4">
    <div class="w-10 h-10 bg-gray-200 rounded-full"></div>
    <div class="flex-1 space-y-2">
      <div class="h-4 bg-gray-200 rounded w-1/3"></div>
      <div class="h-3 bg-gray-200 rounded w-1/4"></div>
    </div>
  </div>
</div>

<!-- Table skeleton -->
<div class="space-y-3 animate-pulse">
  <div class="h-10 bg-gray-200 rounded"></div>
  <div class="h-10 bg-gray-200 rounded"></div>
  <div class="h-10 bg-gray-200 rounded"></div>
</div>
```
