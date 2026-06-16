export type ImportState =
  | 'idle'
  | 'uploading'
  | 'analyzing'
  | 'preview'
  | 'importing'
  | 'success'
  | 'error'

export interface PreviewData {
  headers: string[]
  rows: Record<string, string>[]
  totalRows: number
  matchedFields: string[]
  unmatchedFields: string[]
}
