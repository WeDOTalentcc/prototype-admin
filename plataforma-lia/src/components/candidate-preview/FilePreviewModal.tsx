"use client"

import { useState } from "react"
import { useModalA11y } from "@/hooks/ui/use-modal-a11y"
import {
  FileText, FileVideo, Mic, ZoomOut, ZoomIn, RotateCw, Download, X,
} from "lucide-react"
import { Image } from "lucide-react"
import { Button } from "@/components/ui/button"

export interface FileItem {
  name: string
  type?: string
  url?: string
  videoType?: string
  audioType?: string
  duration?: string
}

interface Candidate {
  avatar_url?: string
  avatar?: string
}

interface FilePreviewModalProps {
  showPreview: boolean
  selectedFile: FileItem | null
  previewType: "pdf" | "image" | "video" | "audio" | null
  onClose: () => void
  candidate: Candidate
}

/**
 * File preview modal — renders the candidate file in browser-native player
 * (iframe / img / video / audio) when the candidate has a real file_url.
 *
 * F7 cleanup (2026-05-23): removed 547 LOC of mock JSX (92%/95% scores,
 * Bruno Carvalho Dias transcription, hardcoded video placeholders) — now
 * a pure file viewer. Real screening/analysis modal is ScreeningMediaModal
 * (canonical, used by candidate-preview/CandidatePreviewModals.tsx).
 */
export function FilePreviewModal({
  showPreview, selectedFile, previewType, onClose, candidate,
}: FilePreviewModalProps) {
  const [imageZoom, setImageZoom] = useState(100)
  const dialogRef = useModalA11y(showPreview, onClose)

  if (!showPreview || !selectedFile) return null

  const fileUrl = selectedFile.url

  return (
    <div
      className="fixed inset-0 bg-black/80 backdrop-blur-sm z-overlay flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label={`Preview: ${selectedFile.name}`}
        className="bg-lia-bg-primary rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-3 bg-lia-bg-primary">
          <div className="flex items-center gap-2">
            {previewType === "pdf" && <FileText className="w-4 h-4 text-lia-text-primary" aria-hidden="true" />}
            {previewType === "image" && <Image className="w-4 h-4 text-lia-text-primary" aria-hidden="true" />}
            {previewType === "video" && <FileVideo className="w-4 h-4 text-status-error" aria-hidden="true" />}
            {previewType === "audio" && <Mic className="w-4 h-4 text-lia-text-tertiary" aria-hidden="true" />}
            <span className="text-sm font-medium text-lia-text-primary">{selectedFile.name}</span>
          </div>

          <div className="flex items-center gap-2">
            {previewType === "image" && (
              <div className="flex items-center gap-1">
                <Button size="sm" variant="ghost" className="p-1 h-6 w-6"
                  onClick={() => setImageZoom(Math.max(25, imageZoom - 25))}
                  aria-label="Diminuir zoom">
                  <ZoomOut className="w-3 h-3" aria-hidden="true" />
                </Button>
                <span className="text-xs text-lia-text-secondary w-10 text-center">{imageZoom}%</span>
                <Button size="sm" variant="ghost" className="p-1 h-6 w-6"
                  onClick={() => setImageZoom(Math.min(200, imageZoom + 25))}
                  aria-label="Aumentar zoom">
                  <ZoomIn className="w-3 h-3" aria-hidden="true" />
                </Button>
                <Button size="sm" variant="ghost" className="p-1 h-6 w-6"
                  onClick={() => setImageZoom(100)}
                  aria-label="Resetar zoom">
                  <RotateCw className="w-3 h-3" aria-hidden="true" />
                </Button>
              </div>
            )}

            {fileUrl && (
              <a href={fileUrl} download={selectedFile.name} target="_blank" rel="noopener noreferrer">
                <Button size="sm" variant="outline" className="gap-1 px-2 py-1 text-xs h-6">
                  <Download className="w-3 h-3" aria-hidden="true" />
                  Baixar
                </Button>
              </a>
            )}

            <Button size="sm" variant="ghost" className="p-1 h-6 w-6"
              onClick={onClose} aria-label="Fechar preview" data-dismiss="true">
              <X className="w-4 h-4" aria-hidden="true" />
            </Button>
          </div>
        </div>

        <div className="p-4 overflow-auto">
          {previewType === "pdf" && (
            fileUrl ? (
              <iframe src={fileUrl} title={selectedFile.name}
                className="w-full h-[70vh] rounded-md border border-lia-border-subtle bg-white" />
            ) : (
              <div className="bg-lia-bg-tertiary rounded-xl p-6 min-h-[400px] flex items-center justify-center">
                <p className="text-lia-text-secondary text-sm">Arquivo não disponível</p>
              </div>
            )
          )}

          {previewType === "image" && (
            <div className="flex items-center justify-center">
              <img
                src={fileUrl || candidate.avatar_url || candidate.avatar}
                alt={selectedFile.name}
                style={{ width: `${imageZoom}%`, maxWidth: "100%" }}
                className="rounded-md transition-colors motion-reduce:transition-none duration-300"
              />
            </div>
          )}

          {previewType === "video" && (
            fileUrl ? (
              <video src={fileUrl} controls className="w-full max-h-[70vh] rounded-md bg-black" />
            ) : (
              <div className="bg-lia-bg-tertiary rounded-xl p-6 min-h-[400px] flex items-center justify-center">
                <p className="text-lia-text-secondary text-sm">Vídeo não disponível</p>
              </div>
            )
          )}

          {previewType === "audio" && (
            fileUrl ? (
              <div className="bg-lia-bg-tertiary rounded-xl p-6 flex items-center justify-center">
                <audio src={fileUrl} controls className="w-full max-w-2xl" />
              </div>
            ) : (
              <div className="bg-lia-bg-tertiary rounded-xl p-6 min-h-[200px] flex items-center justify-center">
                <p className="text-lia-text-secondary text-sm">Áudio não disponível</p>
              </div>
            )
          )}
        </div>
      </div>
    </div>
  )
}
