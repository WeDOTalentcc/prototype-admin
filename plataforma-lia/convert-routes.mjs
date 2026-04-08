import { readFileSync, writeFileSync, readdirSync, statSync } from "fs";
import { join, relative } from "path";

const BASE = "/home/runner/workspace/plataforma-lia/src/app/api/backend-proxy";
const DRY_RUN = process.argv.includes("--dry-run");

function findRouteFiles(dir) {
  const results = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const stat = statSync(full);
    if (stat.isDirectory()) results.push(...findRouteFiles(full));
    else if (entry === "route.ts") results.push(full);
  }
  return results;
}

function extractMethods(content) {
  const methods = [];
  if (/export\s+async\s+function\s+GET/.test(content)) methods.push("GET");
  if (/export\s+async\s+function\s+POST/.test(content)) methods.push("POST");
  if (/export\s+async\s+function\s+PUT/.test(content)) methods.push("PUT");
  if (/export\s+async\s+function\s+DELETE/.test(content)) methods.push("DELETE");
  if (/export\s+async\s+function\s+PATCH/.test(content)) methods.push("PATCH");
  return methods;
}

function hasAuth(content) {
  return content.includes("from \"@/lib/api/auth-headers\"") || content.includes("from '@/lib/api/auth-headers'");
}

function isAlreadyConverted(content) {
  return content.includes("createProxyHandlers");
}

function hasFormData(content) {
  return /formData|FormData|multipart/i.test(content);
}

function hasCatchAll(relPath) {
  return relPath.includes("[...");
}

function hasCustomHeaders(content) {
  return content.includes("X-Company-ID") || content.includes("X-User-ID") || content.includes("X-Admin-Key");
}

function hasRealValidation(content) {
  if (!/(validateBody|validateQuery)/.test(content)) return false;
  const hasPassthrough = content.includes("z.record(z.string(), z.unknown())");
  if (content.includes("validateQuery") && !hasPassthrough) return true;
  if (content.includes("validateBody") && !hasPassthrough) return true;
  return false;
}

function hasResponseTransform(content) {
  return /response\.text\(\)|Content-Disposition|text\/csv/.test(content);
}

function hasRequiredParamValidation(content) {
  return /if\s*\(\s*![a-zA-Z_]+\s*\)\s*\{[^}]*(?:status:\s*400|400\s*\))/.test(content);
}

function hasBodyToUrlTransform(content) {
  const bodyDestructure = content.match(/const\s*\{([^}]+)\}\s*=\s*(?:body|await\s+request\.json\(\))/);
  if (!bodyDestructure) return false;
  const vars = bodyDestructure[1].split(",").map(v => v.trim().split(":")[0].trim().split("=")[0].trim());
  for (const v of vars) {
    if (content.match(new RegExp("(?:url|backendUrl|BACKEND_URL)[^;]*\\$\\{" + v + "\\}"))) return true;
  }
  return false;
}

function hasConditionalUrl(content) {
  return /let\s+url\s*=/.test(content) && /url\s*\+=/.test(content);
}

function hasSelectiveParamForwarding(content) {
  return /new\s+URLSearchParams\(\)/.test(content) && /\.(?:append|set)\(/.test(content);
}

function extractParamsFromRoute(relPath) {
  const params = [];
  const matches = relPath.matchAll(/\[(\w+)\]/g);
  for (const m of matches) params.push(m[1]);
  return params;
}

function extractAllBackendPaths(content, relPath) {
  const routeParams = extractParamsFromRoute(relPath);
  const paths = new Set();

  const urlDefs = content.matchAll(/`\$\{(?:BACKEND_URL|backendUrl)\}(\/[^`]*)`/g);

  for (const match of urlDefs) {
    let path = match[1];

    // Remove trailing query strings and template expressions for query/search params
    // Handle: ?xxx, ${queryString}, ${searchParams}, ${params.toString()}, ${force ? '...' : ''}
    // Strategy: find the FIRST occurrence of ? or ${ that looks like a query param appendage
    // and chop everything after it

    // First, handle explicit query strings
    const qIdx = path.indexOf("?");
    if (qIdx >= 0) path = path.substring(0, qIdx);

    // Handle ${xxx} at the end that are query-related
    path = path.replace(/\$\{(?:searchParams|queryString|params\.toString\(\)|query|qs|force|newName)[^}]*\}.*$/, "");

    // Handle conditional expressions ${xxx ? yyy : zzz}
    path = path.replace(/\$\{[^}]*\?[^}]*:[^}]*\}$/g, "");

    // Replace param interpolations
    let hasUnknownParam = false;
    path = path.replace(/\$\{(?:params\.|resolvedParams\.)?(\w+)\}/g, (_, name) => {
      if (routeParams.includes(name)) return ":" + name;
      // Check if declared from await params
      if (content.match(new RegExp("const\\s*\\{[^}]*\\b" + name + "\\b[^}]*\\}\\s*=\\s*(?:await\\s+)?params"))) {
        return ":" + name;
      }
      hasUnknownParam = true;
      return "UNKNOWN";
    });

    if (path.includes("UNKNOWN") || hasUnknownParam) continue;

    // Remove any remaining ${...}
    if (/\$\{/.test(path)) continue;

    path = path.replace(/\/+/g, "/").replace(/\/$/, "");
    if (path && path.startsWith("/")) paths.add(path);
  }

  return [...paths];
}

function isValidPath(path) {
  // Path should only contain alphanumeric, hyphens, underscores, colons (params), and slashes
  return /^\/[a-zA-Z0-9/:_-]+$/.test(path);
}

function generateConversion(backendPath, methods, auth) {
  const methodsStr = methods.length === 1 && methods[0] === "GET"
    ? ""
    : '\n  methods: [' + methods.map(m => '"' + m + '"').join(", ") + '],';
  const authStr = auth ? "" : "\n  auth: false,";

  return 'import { createProxyHandlers } from "@/lib/api/proxy-handler"\n\nexport const { dynamic, ' + methods.join(", ") + ' } = createProxyHandlers({\n  backendPath: "' + backendPath + '",' + methodsStr + authStr + '\n})\n';
}

// Main
const routes = findRouteFiles(BASE);
const convertible = [];
const skipped = [];
let totalLinesBefore = 0;

for (const file of routes) {
  const content = readFileSync(file, "utf-8");
  const lines = content.split("\n").length;
  const relPath = relative(BASE, file);

  if (isAlreadyConverted(content)) continue;
  if (lines <= 10) continue;

  totalLinesBefore += lines;

  if (hasFormData(content)) { skipped.push({ file: relPath, reason: "file upload" }); continue; }
  if (hasCatchAll(relPath)) { skipped.push({ file: relPath, reason: "catch-all route" }); continue; }
  if (hasResponseTransform(content)) { skipped.push({ file: relPath, reason: "response transform" }); continue; }
  if (hasCustomHeaders(content)) { skipped.push({ file: relPath, reason: "custom auth headers" }); continue; }
  if (hasRealValidation(content)) { skipped.push({ file: relPath, reason: "real Zod validation" }); continue; }
  if (hasBodyToUrlTransform(content)) { skipped.push({ file: relPath, reason: "body-to-URL transform" }); continue; }
  if (hasConditionalUrl(content)) { skipped.push({ file: relPath, reason: "conditional URL" }); continue; }
  if (hasRequiredParamValidation(content)) { skipped.push({ file: relPath, reason: "required param check" }); continue; }
  if (hasSelectiveParamForwarding(content)) { skipped.push({ file: relPath, reason: "selective param forwarding" }); continue; }

  const methods = extractMethods(content);
  if (methods.length === 0) { skipped.push({ file: relPath, reason: "no methods found" }); continue; }

  const auth = hasAuth(content);
  const backendPaths = extractAllBackendPaths(content, relPath);

  if (backendPaths.length === 0) {
    skipped.push({ file: relPath, reason: "cannot extract backend path" });
    continue;
  }

  const uniquePaths = [...new Set(backendPaths)];
  if (uniquePaths.length > 1) {
    skipped.push({ file: relPath, reason: "multiple backend paths: " + uniquePaths.join(", ") });
    continue;
  }

  const backendPath = uniquePaths[0];

  if (!isValidPath(backendPath)) {
    skipped.push({ file: relPath, reason: "invalid path chars: " + backendPath });
    continue;
  }

  convertible.push({ file, relPath, backendPath, methods, auth, lines });
}

console.log("=== CONVERSION SUMMARY ===");
console.log("Convertible: " + convertible.length);
console.log("Skipped: " + skipped.length);
console.log("Total lines before (unconverted): " + totalLinesBefore);
console.log("");

console.log("=== ALL CONVERTIBLE ===");
for (const r of convertible) {
  console.log("  " + r.relPath + " -> " + r.backendPath + " [" + r.methods.join(",") + "] auth=" + r.auth + " (" + r.lines + " lines)");
}

if (!DRY_RUN) {
  let converted = 0;
  let linesAfter = 0;

  for (const route of convertible) {
    const newContent = generateConversion(route.backendPath, route.methods, route.auth);
    writeFileSync(route.file, newContent);
    converted++;
    linesAfter += newContent.split("\n").length;
  }

  const linesBefore = convertible.reduce((s, r) => s + r.lines, 0);
  console.log("\n=== RESULTS ===");
  console.log("Converted: " + converted + " routes");
  console.log("Lines before (these routes): " + linesBefore);
  console.log("Lines after: " + linesAfter);
  console.log("Lines saved: " + (linesBefore - linesAfter));
} else {
  console.log("\n[DRY RUN - no files changed]");
}

console.log("\n=== SKIPPED (" + skipped.length + ") by reason ===");
const reasons = {};
for (const s of skipped) {
  const r = s.reason.startsWith("multiple backend") ? "multiple backend paths" :
            s.reason.startsWith("invalid path") ? "invalid path chars" : s.reason;
  reasons[r] = (reasons[r] || 0) + 1;
}
for (const [reason, count] of Object.entries(reasons).sort((a, b) => b[1] - a[1])) {
  console.log("  " + reason + ": " + count);
}
