#!/usr/bin/env node
import fs from 'node:fs'
import path from 'node:path'

const ROOT = path.resolve('plataforma-lia/src')

const VARIANT_MAP = {
  outline: { variant: 'neutral', muted: false },
  secondary: { variant: 'neutral', muted: true },
  default: { variant: 'neutral', muted: true },
  destructive: { variant: 'danger', muted: false },
  danger: { variant: 'danger', muted: false },
  success: { variant: 'success', muted: false },
  warning: { variant: 'warning', muted: false },
  info: { variant: 'info', muted: false },
}

function walk(dir, files = []) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name)
    if (e.isDirectory()) {
      if (e.name === 'node_modules' || e.name === '.next' || e.name === '__tests__') continue
      walk(p, files)
    } else if (/\.(tsx?|jsx?)$/.test(e.name)) {
      files.push(p)
    }
  }
  return files
}

function findMatchingClose(src, openEnd, openTagName) {
  // src[openEnd] is just past the '>' of the opening tag
  let depth = 1
  const re = new RegExp(`<\\/?${openTagName}\\b[^>]*>`, 'g')
  re.lastIndex = openEnd
  let m
  while ((m = re.exec(src))) {
    if (m[0].startsWith('</')) {
      depth--
      if (depth === 0) return { start: m.index, end: re.lastIndex }
    } else {
      // self-closing? if ends with /> ignore depth change
      if (!m[0].endsWith('/>')) depth++
    }
  }
  return null
}

function transformOpeningTag(tag, fileResult) {
  // tag like `<Badge variant="outline" className="..." key={x}>` or `<Badge ... />`
  const selfClosing = tag.endsWith('/>')
  const inner = selfClosing ? tag.slice(6, -2) : tag.slice(6, -1)
  // Extract variant attribute
  let variantValue = null
  const variantStringMatch = inner.match(/\bvariant="([^"]+)"/)
  const variantExprMatch = inner.match(/\bvariant=\{[^}]*\}/)
  if (variantStringMatch) variantValue = variantStringMatch[1]

  // If variant is a JS expression we can't safely map it -> skip
  if (variantExprMatch && !variantStringMatch) {
    fileResult.skipped++
    return null
  }

  const mapping = variantValue
    ? VARIANT_MAP[variantValue]
    : VARIANT_MAP.default

  if (!mapping) {
    // unknown variant string (e.g. "lilac") -> skip
    fileResult.skipped++
    return null
  }

  let newInner = inner
  if (variantStringMatch) {
    newInner = newInner.replace(/\bvariant="[^"]+"/, `variant="${mapping.variant}"`)
  } else {
    // no variant attr - add one right after Chip
    newInner = ` variant="${mapping.variant}"` + newInner
  }
  if (mapping.muted && !/\bmuted\b/.test(newInner)) {
    // insert after variant attribute
    newInner = newInner.replace(/(variant="[^"]+")/, '$1 muted')
  }

  // Normalize whitespace just in case (don't try too hard)
  return `<Chip${newInner}${selfClosing ? ' />' : '>'}`
}

function migrateFile(file) {
  let src = fs.readFileSync(file, 'utf8')
  if (!/from\s*["']@\/components\/ui\/badge["']/.test(src)) return null

  const fileResult = { file, converted: 0, skipped: 0 }

  // Find all <Badge ...> or <Badge .../> opening tags
  const openRe = /<Badge\b[^>]*?\/?>/g
  // Build list of replacements (start, end, newText)
  const repls = []
  let m
  while ((m = openRe.exec(src))) {
    const tag = m[0]
    const start = m.index
    const end = openRe.lastIndex
    const isSelf = tag.endsWith('/>')
    const newOpen = transformOpeningTag(tag, fileResult)
    if (!newOpen) continue
    if (isSelf) {
      repls.push({ start, end, text: newOpen })
    } else {
      const close = findMatchingClose(src, end, 'Badge')
      if (!close) {
        fileResult.skipped++
        continue
      }
      repls.push({ start, end, text: newOpen })
      repls.push({ start: close.start, end: close.end, text: '</Chip>' })
    }
    fileResult.converted++
  }

  if (repls.length === 0) return fileResult

  // Apply replacements from end to start
  repls.sort((a, b) => b.start - a.start)
  for (const r of repls) {
    src = src.slice(0, r.start) + r.text + src.slice(r.end)
  }

  // Determine if any <Badge> remains; if not, replace import
  const badgeRemains = /<Badge\b/.test(src)
  if (!badgeRemains) {
    // Replace named import lines: `import { Badge } from '...'` (only Badge) -> Chip
    src = src.replace(
      /import\s*\{\s*Badge\s*\}\s*from\s*(["'])@\/components\/ui\/badge\1/g,
      `import { Chip } from $1@/components/ui/chip$1`,
    )
    // Combined imports: `import { Badge, X } from '@/components/ui/badge'`
    src = src.replace(
      /import\s*\{\s*([^}]*)\s*\}\s*from\s*(["'])@\/components\/ui\/badge\2/g,
      (full, names, q) => {
        const list = names.split(',').map((s) => s.trim()).filter(Boolean)
        const without = list.filter((n) => n !== 'Badge')
        const lines = []
        if (without.length > 0) {
          lines.push(`import { ${without.join(', ')} } from ${q}@/components/ui/badge${q}`)
        }
        lines.push(`import { Chip } from ${q}@/components/ui/chip${q}`)
        return lines.join('\n')
      },
    )
  } else {
    // Add Chip import alongside if not already present
    if (!/from\s*["']@\/components\/ui\/chip["']/.test(src)) {
      src = src.replace(
        /(import\s*\{[^}]*Badge[^}]*\}\s*from\s*["']@\/components\/ui\/badge["'])/,
        `$1\nimport { Chip } from "@/components/ui/chip"`,
      )
    }
  }

  fs.writeFileSync(file, src)
  return fileResult
}

const files = walk(ROOT)
let totalConverted = 0
let totalSkipped = 0
let filesTouched = 0
for (const f of files) {
  const r = migrateFile(f)
  if (!r) continue
  if (r.converted > 0) {
    filesTouched++
    totalConverted += r.converted
  }
  totalSkipped += r.skipped
  if (r.skipped > 0) {
    console.log(`SKIP ${r.skipped} in ${path.relative(process.cwd(), r.file)}`)
  }
}
console.log(`\nDone. Files modified: ${filesTouched}, tags converted: ${totalConverted}, skipped: ${totalSkipped}`)
