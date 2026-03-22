"use client"

import { motion } from "framer-motion"

interface FloatingCloudProps {
  style?: React.CSSProperties
  size?: "sm" | "md" | "lg" | "xl"
  duration?: number
  delay?: number
  direction?: "left" | "right"
}

function FloatingCloud({
  style = {},
  size = "md",
  duration = 30,
  delay = 0,
  direction = "right",
}: FloatingCloudProps) {
  const sizes = {
    sm: { width: 150, height: 80 },
    md: { width: 250, height: 130 },
    lg: { width: 350, height: 180 },
    xl: { width: 500, height: 250 },
  }

  const { width, height } = sizes[size]
  const travelDistance = 1800 + width

  return (
    <motion.div
      className="absolute pointer-events-none"
      style={{ width, height, ...style }}
      initial={{ x: direction === "right" ? -width : travelDistance }}
      animate={{ x: direction === "right" ? travelDistance : -width }}
      transition={{
        duration,
        ease: "linear",
        repeat: Infinity,
        delay,
      }}
    >
      <svg
        viewBox="0 0 200 100"
        className="w-full h-full"
        style={{ filter: "blur(2px)" }}
      >
        <defs>
          <radialGradient id={`cloud-grad-${delay}-${size}`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="white" stopOpacity="0.85" />
            <stop offset="40%" stopColor="white" stopOpacity="0.6" />
            <stop offset="70%" stopColor="white" stopOpacity="0.25" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </radialGradient>
        </defs>
        <ellipse cx="100" cy="50" rx="85" ry="42" fill={`url(#cloud-grad-${delay}-${size})`} />
        <ellipse cx="55" cy="55" rx="50" ry="32" fill={`url(#cloud-grad-${delay}-${size})`} />
        <ellipse cx="145" cy="55" rx="55" ry="35" fill={`url(#cloud-grad-${delay}-${size})`} />
        <ellipse cx="80" cy="38" rx="40" ry="28" fill={`url(#cloud-grad-${delay}-${size})`} />
        <ellipse cx="120" cy="40" rx="45" ry="30" fill={`url(#cloud-grad-${delay}-${size})`} />
      </svg>
    </motion.div>
  )
}

export default function CloudsBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
      {/* Gradiente de céu — idêntico ao website wedotalent.cc */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(180deg, #7CBAD8 0%, #8EC5DE 20%, #A3D0E5 40%, #BCE0F0 60%, #D8EEF7 80%, #EDF7FB 95%, #ffffff 100%)",
        }}
      />

      {/* Nuvens SVG animadas — camada de profundidade */}
      <FloatingCloud size="lg"  style={{ top: "8%"  }} duration={35} delay={0}  direction="right" />
      <FloatingCloud size="md"  style={{ top: "22%" }} duration={28} delay={12} direction="left"  />
      <FloatingCloud size="xl"  style={{ top: "35%" }} duration={50} delay={4}  direction="right" />
      <FloatingCloud size="lg"  style={{ top: "50%" }} duration={38} delay={18} direction="left"  />
      <FloatingCloud size="md"  style={{ top: "62%" }} duration={32} delay={8}  direction="right" />
      <FloatingCloud size="xl"  style={{ top: "72%" }} duration={45} delay={2}  direction="left"  />
      <FloatingCloud size="lg"  style={{ top: "82%" }} duration={40} delay={14} direction="right" />
      <FloatingCloud size="sm"  style={{ top: "15%" }} duration={22} delay={6}  direction="left"  />
      <FloatingCloud size="sm"  style={{ top: "55%" }} duration={25} delay={20} direction="right" />

      {/* Fade suave na base */}
      <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-white/50 to-transparent" />
    </div>
  )
}
