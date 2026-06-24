"use client"

import React, { useState, useRef, useCallback, useEffect } from "react"
import { Play, Pause } from "lucide-react"
import { cn } from "@/lib/utils"

interface AudioPlayerProps {
  src: string
  className?: string
  onPlay?: () => void
  onPause?: () => void
  onEnded?: () => void
  autoPlay?: boolean
}

export function AudioPlayer({
  src,
  className,
  onPlay,
  onPause,
  onEnded,
  autoPlay = false,
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isLoaded, setIsLoaded] = useState(false)
  const progressBarRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const audio = new Audio(src)
    audioRef.current = audio

    const handleLoadedMetadata = () => {
      setDuration(audio.duration)
      setIsLoaded(true)
      if (autoPlay) {
        audio.play().catch(() => {})
      }
    }

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime)
    }

    const handleEnded = () => {
      setIsPlaying(false)
      setCurrentTime(0)
      onEnded?.()
    }

    const handlePlay = () => {
      setIsPlaying(true)
      onPlay?.()
    }

    const handlePause = () => {
      setIsPlaying(false)
      onPause?.()
    }

    audio.addEventListener("loadedmetadata", handleLoadedMetadata)
    audio.addEventListener("timeupdate", handleTimeUpdate)
    audio.addEventListener("ended", handleEnded)
    audio.addEventListener("play", handlePlay)
    audio.addEventListener("pause", handlePause)

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata)
      audio.removeEventListener("timeupdate", handleTimeUpdate)
      audio.removeEventListener("ended", handleEnded)
      audio.removeEventListener("play", handlePlay)
      audio.removeEventListener("pause", handlePause)
      audio.pause()
      audio.src = ""
    }
  }, [src, autoPlay, onPlay, onPause, onEnded])

  const togglePlayPause = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return

    if (isPlaying) {
      audio.pause()
    } else {
      audio.play().catch(() => {})
    }
  }, [isPlaying])

  const handleProgressClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const audio = audioRef.current
      const bar = progressBarRef.current
      if (!audio || !bar || !duration) return

      const rect = bar.getBoundingClientRect()
      const clickX = e.clientX - rect.left
      const ratio = Math.max(0, Math.min(1, clickX / rect.width))
      audio.currentTime = ratio * duration
    },
    [duration]
  )

  const formatTime = (seconds: number): string => {
    if (!isFinite(seconds) || seconds < 0) return "0:00"
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, "0")}`
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div
      className={cn(
 "flex items-center gap-2 px-3 py-2 rounded-md bg-lia-bg-secondary border border-lia-border-subtle min-w-sidebar-content max-w-[280px]",
        className
      )}
    >
      <button
        type="button"
        onClick={togglePlayPause}
        disabled={!isLoaded}
        className={cn(
 "flex-shrink-0 w-8 h-8 rounded-md flex items-center justify-center transition-colors",
          isLoaded
            ? "bg-lia-btn-primary-bg text-lia-btn-primary-text hover:bg-lia-btn-primary-hover"
            : "bg-lia-border-default text-lia-text-tertiary cursor-not-allowed"
        )}
        aria-label={isPlaying ? "Pausar áudio" : "Reproduzir áudio"}
      >
        {isPlaying ? (
          <Pause className="w-4 h-4" />
        ) : (
          <Play className="w-4 h-4 ml-0.5" />
        )}
      </button>

      <div className="flex-1 flex flex-col gap-1 min-w-0">
        <div
          ref={progressBarRef}
          onClick={handleProgressClick}
          className="h-1.5 bg-lia-interactive-active dark:bg-lia-bg-elevated rounded-full cursor-pointer relative overflow-hidden"
          role="progressbar"
          aria-valuenow={currentTime}
          aria-valuemin={0}
          aria-valuemax={duration}
        >
          <div
            className="absolute inset-y-0 left-0 bg-lia-btn-primary-bg rounded-full transition-[width] duration-100"
            style={{width: `${progress}%`}}
          />
        </div>
        <div className="flex justify-between text-micro font-['Inter',sans-serif] text-lia-text-muted tabular-nums">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>
    </div>
  )
}
