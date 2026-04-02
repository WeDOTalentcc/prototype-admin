"use client"

import React from "react"
import { Label } from "@/components/ui/label"
import { textStyles } from '@/lib/design-tokens'

interface BigFiveScores {
  openness: number
  conscientiousness: number
  extraversion: number
  agreeableness: number
  stability: number
}

interface BigFiveRadarProps {
  scores: BigFiveScores
  onScoresChange?: (scores: BigFiveScores) => void
  isEditable?: boolean
  size?: number
}

const TRAITS = [
  { key: "openness", label: "Abertura", description: "Inovação e criatividade" },
  { key: "conscientiousness", label: "Conscienciosidade", description: "Processos e organização" },
  { key: "extraversion", label: "Extroversão", description: "Colaboração e energia" },
  { key: "agreeableness", label: "Amabilidade", description: "Empatia e trabalho em equipe" },
  { key: "stability", label: "Estabilidade", description: "Resiliência e calma" }
] as const

export function BigFiveRadar({ 
  scores, 
  onScoresChange, 
  isEditable = false,
  size = 200 
}: BigFiveRadarProps) {
  const center = size / 2
  const maxRadius = (size / 2) - 30
  const angleStep = (2 * Math.PI) / 5
  const startAngle = -Math.PI / 2

  const getPoint = (index: number, value: number): { x: number; y: number } => {
    const angle = startAngle + index * angleStep
    const radius = (value / 100) * maxRadius
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle)
    }
  }

  const getLabelPoint = (index: number): { x: number; y: number } => {
    const angle = startAngle + index * angleStep
    const radius = maxRadius + 20
    return {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle)
    }
  }

  const dataPoints = Object.values(scores)
  const polygonPoints = dataPoints
    .map((value, index) => {
      const point = getPoint(index, value)
      return `${point.x},${point.y}`
    })
    .join(" ")

  const gridLevels = [20, 40, 60, 80, 100]

  const handleSliderChange = (key: keyof BigFiveScores, value: number) => {
    if (onScoresChange) {
      onScoresChange({
        ...scores,
        [key]: value
      })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-center">
        <svg 
          width={size} 
          height={size} 
          viewBox={`0 0 ${size} ${size}`}
          className="overflow-visible"
        >
          {gridLevels.map((level) => {
            const gridPoints = TRAITS.map((_, index) => {
              const point = getPoint(index, level)
              return `${point.x},${point.y}`
            }).join(" ")
            return (
              <polygon
                key={level}
                points={gridPoints}
                fill="none"
                stroke="currentColor"
                strokeWidth="1"
                className="text-lia-text-disabled"
              />
            )
          })}

          {TRAITS.map((_, index) => {
            const point = getPoint(index, 100)
            return (
              <line
                key={`trait-line-${index}`}
                x1={center}
                y1={center}
                x2={point.x}
                y2={point.y}
                stroke="currentColor"
                strokeWidth="1"
                className="text-lia-text-disabled"
              />
            )
          })}

          <defs>
            <linearGradient id="radarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="var(--gray-600)" stopOpacity="0.4" />
              <stop offset="100%" stopColor="var(--wedo-cyan)" stopOpacity="0.4" />
            </linearGradient>
          </defs>
          <polygon
            points={polygonPoints}
            fill="url(#radarGradient)"
            stroke="var(--gray-600)"
            strokeWidth="2"
            className="transition-colors motion-reduce:transition-none duration-300"
          />

          {dataPoints.map((value, index) => {
            const point = getPoint(index, value)
            return (
              <circle
                key={`data-point-${index}`}
                cx={point.x}
                cy={point.y}
                r="4"
                fill="var(--gray-600)"
                stroke="white"
                strokeWidth="2"
                className="transition-colors motion-reduce:transition-none duration-300"
              />
            )
          })}

          {TRAITS.map((trait, index) => {
            const labelPoint = getLabelPoint(index)
            const isTop = index === 0
            const isRight = index === 1 || index === 2
            const textAnchor = isTop ? "middle" : isRight ? "start" : "end"
            const dy = isTop ? -5 : index === 2 || index === 3 ? 5 : 0
            
            return (
              <text
                key={trait.key}
                x={labelPoint.x}
                y={labelPoint.y + dy}
                textAnchor={textAnchor}
                className="text-xs font-medium fill-gray-600 dark:lia-fill-400 font-['Open_Sans',sans-serif]"
              >
                {trait.label}
              </text>
            )
          })}
        </svg>
      </div>

      {isEditable && (
        <div className="space-y-4 mt-4">
          {TRAITS.map((trait) => (
            <div key={trait.key} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label className={textStyles.label}>
                  {trait.label}
                </Label>
                <span className="text-xs font-semibold text-lia-text-primary">
                  {scores[trait.key]}%
                </span>
              </div>
              <p className={textStyles.description}>
                {trait.description}
              </p>
              <input
                type="range"
                min="0"
                max="100"
                value={scores[trait.key]}
                onChange={(e) => handleSliderChange(trait.key, parseInt(e.target.value))}
                className="w-full h-1.5 bg-gray-200 dark:bg-lia-bg-elevated rounded-md appearance-none cursor-pointer accent-gray-900 dark:lia-accent-100"
              />
            </div>
          ))}
        </div>
      )}

      {!isEditable && (
        <div className="grid grid-cols-5 gap-2 text-center">
          {TRAITS.map((trait) => (
            <div key={trait.key} className="space-y-1">
              <div className="text-sm font-bold text-lia-text-primary">
                {scores[trait.key]}%
              </div>
              <div className={textStyles.description}>
                {trait.label.substring(0, 4)}.
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
