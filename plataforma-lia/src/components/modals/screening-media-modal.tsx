"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState, useRef, useEffect } from"react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from"@/components/ui/dialog"
import { VisuallyHidden } from"@radix-ui/react-visually-hidden"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { ScrollArea } from"@/components/ui/scroll-area"
import {
  X, Download, Play, Pause, Volume2, VolumeX,
  Mic, Video, Brain, Target, FileText, ChevronRight
} from"lucide-react"
import { textStyles } from"@/lib/design-tokens"
import { useTranslations } from "next-intl"

export interface ScreeningQuestion {
  id: number
  question: string
  duration?: string
  transcription: string
  timestamp?: string
  analysis?: {
    sentiment: 'positive' | 'neutral' | 'negative'
    keywords: string[]
    score: number
  }
}

export interface TranscriptionSegment {
  timestamp: string
  speaker: 'Candidato' | 'Entrevistador' | 'Sistema'
  text: string
}

export interface ScreeningMediaModalProps {
  isOpen: boolean
  onClose: () => void
  type: 'audio' | 'video'
  title: string
  fileName?: string
  fileSize?: string
  duration: string
  mediaUrl?: string
  jobTitle?: string
  candidateName?: string
  screeningType?: 'voice' | 'text' | 'video'
  questions: ScreeningQuestion[]
  transcription?: TranscriptionSegment[]
  highlights?: string[]
  onDownload?: () => void
  onOpenFullEvaluation?: () => void
}

export function ScreeningMediaModal({
  isOpen,
  onClose,
  type,
  title,
  fileName,
  fileSize,
  duration,
  mediaUrl,
  jobTitle,
  candidateName,
  screeningType = 'voice',
  questions,
  transcription,
  highlights,
  onDownload,
  onOpenFullEvaluation
}: ScreeningMediaModalProps) {
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('screening-media', isOpen)

  const t = useTranslations('screening')
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [totalDuration, setTotalDuration] = useState(0)
  const mediaRef = useRef<HTMLAudioElement | HTMLVideoElement>(null)

  useEffect(() => {
    if (!isOpen) {
      setIsPlaying(false)
      setCurrentTime(0)
    }
  }, [isOpen])

  const togglePlay = () => {
    if (mediaRef.current) {
      if (isPlaying) {
        mediaRef.current.pause()
      } else {
        mediaRef.current.play()
      }
      setIsPlaying(!isPlaying)
    }
  }

  const toggleMute = () => {
    if (mediaRef.current) {
      mediaRef.current.muted = !isMuted
      setIsMuted(!isMuted)
    }
  }

  const handleTimeUpdate = () => {
    if (mediaRef.current) {
      setCurrentTime(mediaRef.current.currentTime)
    }
  }

  const handleLoadedMetadata = () => {
    if (mediaRef.current) {
      setTotalDuration(mediaRef.current.duration)
    }
  }

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const time = parseFloat(e.target.value)
    if (mediaRef.current) {
      mediaRef.current.currentTime = time
      setCurrentTime(time)
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const parseDuration = (dur: string): number => {
    const parts = dur.split(':')
    if (parts.length === 2) {
      return parseInt(parts[0]) * 60 + parseInt(parts[1])
    }
    return 0
  }

  const displayDuration = totalDuration > 0 ? totalDuration : parseDuration(duration)

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] p-0 gap-0 overflow-hidden flex flex-col" data-testid="screening-media-modal">
        <DialogHeader className="px-6 py-4 flex flex-row items-center justify-between">
          <div className="flex items-center gap-3">
            {type === 'audio' ? (
              <Mic className="w-5 h-5 text-lia-text-secondary" />
            ) : (
              <Video className="w-5 h-5 text-wedo-purple" />
            )}
            <DialogTitle className={`${textStyles.titleLarge} flex items-center gap-2`}>
              {title}
              {fileName && (
                <span className="text-lia-text-tertiary font-normal text-sm">{fileName}</span>
              )}
            </DialogTitle>
            <VisuallyHidden>
              <DialogDescription>
                {type === 'audio' ? t('media.dialogDescriptionAudio') : t('media.dialogDescriptionVideo')}
              </DialogDescription>
            </VisuallyHidden>
          </div>
          <div className="flex items-center gap-2">
            {onDownload && (
              <Button variant="outline" size="sm" onClick={onDownload} className="gap-1.5">
                <Download className="w-4 h-4" />
                {t('media.download')}
              </Button>
            )}
            <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
              <X className="w-4 h-4" />
            </Button>
          </div>
        </DialogHeader>

        <div className="flex flex-1 min-h-0 overflow-hidden">
          <div className="flex-1 p-6 space-y-6 overflow-y-auto border-r border-lia-border-subtle">
            <div className="flex flex-col items-center justify-center py-8 bg-gradient-to-b from-lia-bg-secondary to-white rounded-xl border border-lia-border-subtle">
              <div className="w-20 h-20 rounded-full bg-lia-bg-tertiary flex items-center justify-center mb-4">
                {type === 'audio' ? (
                  <Mic className="w-10 h-10 text-lia-text-secondary" />
                ) : (
                  <Video className="w-10 h-10 text-wedo-purple" />
                )}
              </div>
              <p className={`${textStyles.body} text-lia-text-secondary mb-1`}>{t('media.clickToPlay')}</p>
              {fileName && <p className={`${textStyles.bodySmall} text-lia-text-tertiary`}>{fileName}</p>}

              {type === 'audio' ? (
                <audio
                  ref={mediaRef as React.RefObject<HTMLAudioElement>}
                  src={mediaUrl}
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={handleLoadedMetadata}
                  onEnded={() => setIsPlaying(false)}
                  className="hidden"
                />
              ) : (
                <video
                  ref={mediaRef as React.RefObject<HTMLVideoElement>}
                  src={mediaUrl}
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={handleLoadedMetadata}
                  onEnded={() => setIsPlaying(false)}
                  className="w-full max-w-md rounded-md mt-4"
                  controls={false}
                />
              )}

              <div className="w-full max-w-md mt-6 px-4">
                <div className="flex items-center gap-3">
                  <Button
                    size="sm"
                    variant="primary"
                    onClick={togglePlay}
                    className="w-10 h-10 rounded-full bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover p-0"
                  >
                    {isPlaying ? (
                      <Pause className="w-5 h-5 text-white" />
                    ) : (
                      <Play className="w-5 h-5 text-white ml-0.5" />
                    )}
                  </Button>
                  <div className="flex-1 relative">
                    <input
                      type="range"
                      min="0"
                      max={displayDuration || 100}
                      value={currentTime}
                      onChange={handleSeek}
                      className="w-full h-2 bg-lia-interactive-active rounded-full appearance-none cursor-pointer accent-lia-btn-primary-bg"
                    />
                  </div>
                  <span className={`${textStyles.bodySmall} text-lia-text-secondary min-w-20 text-right`}>
                    {formatTime(currentTime)} / {duration}
                  </span>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={toggleMute}
                    className="w-8 h-8 p-0"
                  >
                    {isMuted ? (
                      <VolumeX className="w-4 h-4 text-lia-text-tertiary" />
                    ) : (
                      <Volume2 className="w-4 h-4 text-lia-text-primary" />
                    )}
                  </Button>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className={`${textStyles.title} flex items-center gap-2`}>
                <FileText className="w-4 h-4 text-lia-text-secondary" />
                {t('media.screeningQuestions')}
              </h3>
              <div className="space-y-2">
                {questions.map((q, idx) => (
                  <div key={q.id} className="flex items-start gap-3 text-sm">
                    <span className="w-5 h-5 rounded-full bg-lia-bg-tertiary flex items-center justify-center text-xs font-medium text-lia-text-primary flex-shrink-0 mt-0.5">
                      {idx + 1}
                    </span>
                    <p className={textStyles.body}>{q.question}</p>
                  </div>
                ))}
              </div>
            </div>

            {onOpenFullEvaluation && (
              <div className="pt-2">
                <Button
                  variant="outline"
                  className="w-full gap-2"
                  onClick={onOpenFullEvaluation}
                >
                  <Target className="w-4 h-4" />
                  {t('media.viewFullWSI')}
                  <ChevronRight className="w-4 h-4 ml-auto" />
                </Button>
              </div>
            )}
          </div>

          <div className="w-[380px] bg-lia-bg-secondary p-4 flex flex-col min-h-0">
            <h3 className={`${textStyles.title} flex items-center gap-2 mb-3`}>
              <FileText className="w-4 h-4 text-lia-text-secondary" />
              {t('media.transcription')}
            </h3>
            
            <div className="mb-3">
              <Chip variant="neutral" className="bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default">
                {type === 'audio' ? t('media.audioScreening') : t('media.videoInterview')}
              </Chip>
              <span className={`${textStyles.caption} ml-2`}>{t('media.duration', { duration })}</span>
            </div>

            <ScrollArea className="flex-1">
              <div className="space-y-3 pr-2">
                {transcription && transcription.length > 0 ? (
                  transcription.map((segment, idx) => (
                    <div key={idx} className="bg-lia-bg-primary p-3 rounded-xl border border-lia-border-subtle">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-micro font-medium text-lia-text-secondary">{segment.timestamp}</span>
                        <span className="text-micro text-lia-text-tertiary">•</span>
                        <span className="text-micro font-medium text-lia-text-primary">{segment.speaker}</span>
                      </div>
                      <p className={`${textStyles.bodySmall} text-lia-text-primary`}>"{segment.text}"</p>
                    </div>
                  ))
                ) : questions.length > 0 ? (
                  questions.map((q, idx) => (
                    <div key={q.id} className="bg-lia-bg-primary p-3 rounded-xl border border-lia-border-subtle">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-micro font-medium text-lia-text-secondary">{q.timestamp || `${idx}:00`}</span>
                        <span className="text-micro text-lia-text-tertiary">•</span>
                        <span className="text-micro font-medium text-lia-text-primary">{t('media.candidate')}</span>
                      </div>
                      <p className={`${textStyles.bodySmall} text-lia-text-primary`}>"{q.transcription}"</p>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-lia-text-tertiary">
                    <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className={textStyles.bodySmall}>{t('media.transcriptionUnavailable')}</p>
                  </div>
                )}
              </div>
            </ScrollArea>

            {highlights && highlights.length > 0 && (
              <div className="mt-4 pt-4 border-t border-lia-border-subtle">
                <h4 className={`${textStyles.label} flex items-center gap-1 mb-2`}>
                  <Brain className="w-3 h-3 text-wedo-cyan" />
                  {t('media.liaHighlights')}
                </h4>
                <div className="space-y-1">
                  {highlights.map((h, idx) => (
                    <div key={idx} className="flex items-start gap-2 text-xs">
                      <ChevronRight className="w-3 h-3 text-lia-text-secondary flex-shrink-0 mt-0.5" />
                      <span className={textStyles.bodySmall}>{h}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default ScreeningMediaModal
