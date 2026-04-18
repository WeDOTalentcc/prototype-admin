#!/usr/bin/env node
import fs from 'node:fs'
import path from 'node:path'

const ROOT = path.resolve('plataforma-lia/src')
function walk(dir, files = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) {
      if (['node_modules', '.next', '__tests__'].includes(e.name)) continue
      walk(p, files)
    } else if (/\.(tsx?|jsx?)$/.test(e.name)) files.push(p)
  }
  return files
}

let touched = 0
for (const f of walk(ROOT)) {
  let src = fs.readFileSync(f, 'utf8')
  if (!/from\s*["']@\/components\/ui\/badge["']/.test(src)) continue
  // Skip the primitive itself
  if (f.endsWith(path.join('src', 'components', 'ui', 'badge.tsx'))) continue
  if (/\bBadge\b/.test(src.replace(/import\s*\{[^}]*\}\s*from\s*["']@\/components\/ui\/badge["'][^\n]*/g, ''))) {
    // Badge is referenced elsewhere (likely as a substring of e.g. CandidateScoreBadge); keep import only if the literal `Badge` token still appears outside import line
    // But we know there are no <Badge> JSX. It might still be used as a type. Check for patterns like ': Badge', '<Badge', 'Badge.'
    const restSrc = src.replace(/import[^\n]*from\s*["']@\/components\/ui\/badge["'][^\n]*\n?/g, '')
    if (/\bBadge\b/.test(restSrc.replace(/[A-Za-z_]Badge|Badge[A-Za-z_]/g, ''))) {
      continue
    }
  }
  // Remove the Badge import line
  const newSrc = src.replace(
    /import\s*\{\s*Badge\s*\}\s*from\s*["']@\/components\/ui\/badge["'];?\s*\n?/g,
    '',
  )
  if (newSrc !== src) {
    fs.writeFileSync(f, newSrc)
    touched++
  }
}
console.log(`Cleaned ${touched} files`)
