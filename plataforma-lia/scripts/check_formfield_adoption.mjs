/**
 * GAP-11-021 — FormField canonical adoption sensor.
 *
 * Detects components with raw htmlFor labels that should use <FormField>.
 * A component "needs FormField" when it has htmlFor attributes but does not
 * import from @/components/ui/form-field.
 *
 * Usage:
 *   node scripts/check_formfield_adoption.mjs          # warn-only
 *   node scripts/check_formfield_adoption.mjs --json   # JSON output
 *
 * Ratchet: run with --max-violations=N to fail above threshold.
 */
import { readFileSync, readdirSync, statSync } from "fs"
import { join, extname } from "path"

const FORM_FIELD_IMPORT = /from ['"]@\/components\/ui\/form-field['"]/
const HTML_FOR_PATTERN = /htmlFor=/
const LABEL_FOR_PATTERN = /<label\s+htmlFor=/i

function walkSync(dir, collected = []) {
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry)
    try {
      const s = statSync(p)
      if (s.isDirectory() && !["node_modules", ".next", "__tests__"].includes(entry)) {
        walkSync(p, collected)
      } else if (s.isFile() && (extname(p) === ".tsx" || extname(p) === ".ts")) {
        collected.push(p)
      }
    } catch { /* skip */ }
  }
  return collected
}

const baseDir = "src/components"
const files = walkSync(baseDir)
const violations = []

for (const file of files) {
  const content = readFileSync(file, "utf-8")
  // Has raw htmlFor usage AND no FormField import
  if ((HTML_FOR_PATTERN.test(content) || LABEL_FOR_PATTERN.test(content)) 
      && !FORM_FIELD_IMPORT.test(content)) {
    // Count how many htmlFor occurrences
    const count = (content.match(/htmlFor=/g) || []).length
    violations.push({ file: file.replace(process.cwd() + "/", ""), count })
  }
}

const total = violations.length
const maxArg = process.argv.find(a => a.startsWith("--max-violations="))
const maxViolations = maxArg ? parseInt(maxArg.split("=")[1]) : Infinity

if (process.argv.includes("--json")) {
  console.log(JSON.stringify({ total_files_needing_formfield: total, violations }, null, 2))
} else {
  if (violations.length > 0) {
    console.log(`⚠️  FormField adoption: ${total} component file(s) use raw htmlFor without FormField`)
    for (const v of violations.slice(0, 15)) {
      console.log(`  ${v.count}x  ${v.file}`)
    }
    if (violations.length > 15) console.log(`  ... and ${violations.length - 15} more`)
  } else {
    console.log("✅ FormField adoption: 0 violations — all form fields use FormField canonical")
  }
}

if (total > maxViolations) {
  process.exit(1)
}
