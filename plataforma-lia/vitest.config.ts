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
          exclude: ['src/hooks/__tests__/**', 'src/hooks/**/__tests__/**'],
          globals: true,
          alias: {
            '@': path.resolve(dirname, 'src'),
          },
        },
      },
      // ── Colocated unit tests (next to source files, no __tests__ dir) ─────
      {
        test: {
          name: 'unit-colocated',
          environment: 'jsdom',
          include: [
            'src/lib/**/*.test.ts',
            'src/utils/**/*.test.ts',
            'src/components/**/*.test.ts',
            'src/components/**/*.test.tsx',
          ],
          exclude: [
            'src/**/__tests__/**',
            'src/hooks/__tests__/**',
          ],
          globals: true,
          setupFiles: ['src/hooks/__tests__/setup.ts'],
          alias: {
            '@': path.resolve(dirname, 'src'),
          },
        },
        esbuild: {
          jsx: 'automatic',
          jsxImportSource: 'react',
        },
      },
      // ── Hook tests (jsdom — precisam de DOM/React context) ────────────────
      {
        test: {
          name: 'hooks',
          environment: 'jsdom',
          include: ['src/hooks/__tests__/**/*.test.ts', 'src/hooks/**/__tests__/**/*.test.ts'],
          globals: true,
          setupFiles: ['src/hooks/__tests__/setup.ts'],
          alias: {
            '@': path.resolve(dirname, 'src'),
          },
        },
        esbuild: {
          jsx: 'automatic',
          jsxImportSource: 'react',
        },
      },
      // ── Component tests (jsdom — React components com JSX) ───────────────
      {
        test: {
          name: 'components',
          environment: 'jsdom',
          include: [
            'src/components/**/__tests__/**/*.test.tsx',
            'src/app/**/__tests__/**/*.test.tsx',
            'src/contexts/**/__tests__/**/*.test.tsx',
          ],
          globals: true,
          setupFiles: ['src/hooks/__tests__/setup.ts'],
          alias: {
            '@': path.resolve(dirname, 'src'),
            // framer-motion nao instalado no ambiente de teste — mock manual preserva DOM.
            'framer-motion': path.resolve(dirname, '__mocks__/framer-motion.tsx'),
          },
        },
        esbuild: {
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
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/**/*.test.{ts,tsx}',
        'src/**/*.stories.{ts,tsx}',
        'src/types/',
        '.next/',
        'out/',
      ],
      thresholds: {
        statements: 35,
        branches: 35,
        functions: 35,
        lines: 35,
      },
    },
  },
});
