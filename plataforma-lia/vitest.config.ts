import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { defineConfig } from 'vitest/config';

import { storybookTest } from '@storybook/addon-vitest/vitest-plugin';

import { playwright } from '@vitest/browser-playwright';

const dirname =
  typeof __dirname !== 'undefined' ? __dirname : path.dirname(fileURLToPath(import.meta.url));

// More info at: https://storybook.js.org/docs/next/writing-tests/integrations/vitest-addon
export default defineConfig({
  test: {
    projects: [
      // ── Unit tests (hooks, utils, pure logic) ─────────────────────────────
      {
        test: {
          name: 'unit',
          environment: 'node',
          include: ['src/**/__tests__/**/*.test.ts'],
          exclude: ['src/hooks/__tests__/**'],
          globals: true,
          alias: {
            '@': path.resolve(dirname, 'src'),
          },
        },
      },
      // ── Hook tests (jsdom — precisam de DOM/React context) ────────────────
      {
        test: {
          name: 'hooks',
          environment: 'jsdom',
          include: ['src/hooks/__tests__/**/*.test.ts'],
          globals: true,
          setupFiles: ['src/hooks/__tests__/setup.ts'],
          alias: {
            '@': path.resolve(dirname, 'src'),
          },
        },
        esbuild: {
          jsxInject: `import React from 'react'`,
          jsx: 'automatic',
          jsxImportSource: 'react',
        },
      },
      // ── Storybook visual tests ─────────────────────────────────────────────
      {
        extends: true,
        plugins: [
          storybookTest({ configDir: path.join(dirname, '.storybook') }),
        ],
        test: {
          name: 'storybook',
          browser: {
            enabled: true,
            headless: true,
            provider: playwright({}),
            instances: [{ browser: 'chromium' }],
          },
          setupFiles: ['.storybook/vitest.setup.ts'],
        },
      },
    ],
  },
});
