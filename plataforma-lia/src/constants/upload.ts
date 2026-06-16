/**
 * File upload constraints — canonical source of truth.
 * Keep in sync with backend: lia-agent-system/app/shared/upload_limits.py
 */

// Primary limit used across all upload surfaces
export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 // 10 MiB
export const MAX_FILE_SIZE_MB = 10

// Alias for legacy imports that use the name MAX_FILE_SIZE
export const MAX_FILE_SIZE = MAX_FILE_SIZE_BYTES

// Accepted MIME types (CV / document uploads)
export const ALLOWED_MIME_TYPES = [
  "application/pdf",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "text/plain",
  "application/vnd.ms-excel",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "image/jpeg",
  "image/png",
]

// Batch upload cap
export const MAX_FILES_PER_BATCH = 5

/**
 * Resolve JD-import file size limit.
 * Reads UPLOAD_JD_MAX_BYTES env var — same variable read by the backend
 * (lia-agent-system/app/shared/upload_limits.py, Audit M-12 / Task #858).
 * Falls back to MAX_FILE_SIZE_BYTES when the env var is absent or invalid.
 */
export function resolveMaxFileSize(): number {
  const raw = process.env.UPLOAD_JD_MAX_BYTES
  if (!raw) return MAX_FILE_SIZE_BYTES
  const parsed = Number(raw)
  if (!Number.isFinite(parsed) || parsed <= 0) return MAX_FILE_SIZE_BYTES
  return Math.floor(parsed)
}
