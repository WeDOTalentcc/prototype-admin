"use client"


type CloudVariant = "A" | "B" | "C" | "D"
type DepthLayer = "back" | "mid" | "front"

interface FloatingCloudProps {
  top: string
  variant?: CloudVariant
  layer?: DepthLayer
  duration?: number
  delay?: number
  direction?: "left" | "right"
  floatVertical?: boolean
}

const LAYER_CONFIG: Record<DepthLayer, { opacity: number; blur: string; scale: number }> = {
  back:  { opacity: 0.30, blur: "blur(3px)", scale: 0.85 },
  mid:   { opacity: 0.60, blur: "blur(2px)", scale: 1.0  },
  front: { opacity: 0.88, blur: "blur(1px)", scale: 1.15 },
}

const SIZE_CONFIG: Record<DepthLayer, { width: number; height: number }> = {
  back:  { width: 280, height: 140 },
  mid:   { width: 380, height: 190 },
  front: { width: 480, height: 240 },
}

function CloudSVG({ variant, gradId }: { variant: CloudVariant; gradId: string }) {
  return (
    <svg viewBox="0 0 240 110" className="w-full h-full">
      <defs>
        <radialGradient id={gradId} cx="50%" cy="60%" r="50%">
          <stop offset="0%"   stopColor="white" stopOpacity="0.95" />
          <stop offset="35%"  stopColor="white" stopOpacity="0.75" />
          <stop offset="65%"  stopColor="white" stopOpacity="0.40" />
          <stop offset="100%" stopColor="white" stopOpacity="0"    />
        </radialGradient>
      </defs>

      {variant === "A" && (
        <>
          <ellipse cx="120" cy="68" rx="100" ry="36" fill={`url(#${gradId})`} />
          <ellipse cx="60"  cy="70" rx="55"  ry="30" fill={`url(#${gradId})`} />
          <ellipse cx="180" cy="68" rx="60"  ry="32" fill={`url(#${gradId})`} />
          <ellipse cx="95"  cy="52" rx="48"  ry="32" fill={`url(#${gradId})`} />
          <ellipse cx="148" cy="48" rx="52"  ry="34" fill={`url(#${gradId})`} />
          <ellipse cx="70"  cy="42" rx="36"  ry="28" fill={`url(#${gradId})`} />
          <ellipse cx="120" cy="36" rx="40"  ry="26" fill={`url(#${gradId})`} />
          <ellipse cx="170" cy="40" rx="38"  ry="26" fill={`url(#${gradId})`} />
          <ellipse cx="200" cy="58" rx="42"  ry="28" fill={`url(#${gradId})`} />
        </>
      )}

      {variant === "B" && (
        <>
          <ellipse cx="115" cy="72" rx="95"  ry="32" fill={`url(#${gradId})`} />
          <ellipse cx="50"  cy="72" rx="50"  ry="28" fill={`url(#${gradId})`} />
          <ellipse cx="190" cy="70" rx="55"  ry="30" fill={`url(#${gradId})`} />
          <ellipse cx="80"  cy="55" rx="50"  ry="34" fill={`url(#${gradId})`} />
          <ellipse cx="140" cy="50" rx="55"  ry="36" fill={`url(#${gradId})`} />
          <ellipse cx="105" cy="38" rx="38"  ry="27" fill={`url(#${gradId})`} />
          <ellipse cx="160" cy="34" rx="42"  ry="28" fill={`url(#${gradId})`} />
          <ellipse cx="55"  cy="46" rx="34"  ry="24" fill={`url(#${gradId})`} />
          <ellipse cx="210" cy="56" rx="36"  ry="26" fill={`url(#${gradId})`} />
          <ellipse cx="30"  cy="62" rx="28"  ry="22" fill={`url(#${gradId})`} />
        </>
      )}

      {variant === "C" && (
        <>
          <ellipse cx="110" cy="70" rx="90"  ry="34" fill={`url(#${gradId})`} />
          <ellipse cx="45"  cy="68" rx="48"  ry="28" fill={`url(#${gradId})`} />
          <ellipse cx="185" cy="66" rx="58"  ry="31" fill={`url(#${gradId})`} />
          <ellipse cx="75"  cy="48" rx="46"  ry="32" fill={`url(#${gradId})`} />
          <ellipse cx="145" cy="44" rx="50"  ry="34" fill={`url(#${gradId})`} />
          <ellipse cx="115" cy="34" rx="36"  ry="25" fill={`url(#${gradId})`} />
          <ellipse cx="165" cy="30" rx="38"  ry="24" fill={`url(#${gradId})`} />
          <ellipse cx="68"  cy="37" rx="32"  ry="22" fill={`url(#${gradId})`} />
          <ellipse cx="205" cy="52" rx="34"  ry="24" fill={`url(#${gradId})`} />
        </>
      )}

      {variant === "D" && (
        <>
          <ellipse cx="125" cy="66" rx="105" ry="38" fill={`url(#${gradId})`} />
          <ellipse cx="55"  cy="70" rx="52"  ry="30" fill={`url(#${gradId})`} />
          <ellipse cx="195" cy="68" rx="50"  ry="29" fill={`url(#${gradId})`} />
          <ellipse cx="88"  cy="50" rx="52"  ry="36" fill={`url(#${gradId})`} />
          <ellipse cx="155" cy="46" rx="56"  ry="37" fill={`url(#${gradId})`} />
          <ellipse cx="100" cy="33" rx="40"  ry="27" fill={`url(#${gradId})`} />
          <ellipse cx="155" cy="30" rx="44"  ry="28" fill={`url(#${gradId})`} />
          <ellipse cx="60"  cy="44" rx="36"  ry="25" fill={`url(#${gradId})`} />
          <ellipse cx="215" cy="56" rx="38"  ry="26" fill={`url(#${gradId})`} />
          <ellipse cx="25"  cy="60" rx="26"  ry="20" fill={`url(#${gradId})`} />
        </>
      )}
    </svg>
  )
}

function FloatingCloud({
  top,
  variant = "A",
  layer = "mid",
  duration = 30,
  delay = 0,
  direction = "right",
  floatVertical = false,
}: FloatingCloudProps) {
  const { width, height } = SIZE_CONFIG[layer]
  const { opacity, blur, scale } = LAYER_CONFIG[layer]
  const gradId = `cg-${variant}-${layer}-${delay}`

  // OPT-027: CSS animation replacing framer-motion infinite translate
  // Uses a unique keyframe name per direction injected via <style>
  const animName = `cloud-drift-${direction === "right" ? "r" : "l"}`
  const floatAnimName = `cloud-float-${Math.round(duration * 0.35)}`

  const animStyle: React.CSSProperties = {
    top,
    width,
    height,
    opacity,
    transform: `scale(${scale})`,
    filter: blur,
    animationName: floatVertical ? `${animName}, ${floatAnimName}` : animName,
    animationDuration: floatVertical
      ? `${duration}s, ${Math.round(duration * 0.35)}s`
      : `${duration}s`,
    animationTimingFunction: floatVertical ? "linear, ease-in-out" : "linear",
    animationDelay: floatVertical ? `${delay}s, ${delay}s` : `${delay}s`,
    animationIterationCount: "infinite",
    animationDirection: floatVertical ? "normal, alternate" : "normal",
  }

  return (
    <div
      className="absolute pointer-events-none"
      style={animStyle}
    >
      <CloudSVG variant={variant} gradId={gradId} />
    </div>
  )
}

export default function CloudsBackground() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none" aria-hidden="true">
      {/* OPT-027: CSS keyframes replacing framer-motion infinite x/y animations */}
      <style>{`
        @keyframes cloud-drift-r {
          from { transform: translateX(-480px) scaleX(1); }
          to   { transform: translateX(calc(100vw + 480px)) scaleX(1); }
        }
        @keyframes cloud-drift-l {
          from { transform: translateX(calc(100vw + 480px)) scaleX(1); }
          to   { transform: translateX(-480px) scaleX(1); }
        }
        @keyframes cloud-float-10 {
          from { transform: translateY(0px); }
          to   { transform: translateY(-10px); }
        }
        @keyframes cloud-float-14 {
          from { transform: translateY(0px); }
          to   { transform: translateY(-10px); }
        }
        @keyframes cloud-float-15 {
          from { transform: translateY(0px); }
          to   { transform: translateY(-10px); }
        }
      `}</style>
      <div
        className="absolute inset-0"
        style={{background:
            "linear-gradient(180deg, #7CBAD8 0%, #8EC5DE 20%, #A3D0E5 40%, #BCE0F0 60%, #D8EEF7 80%, #EDF7FB 95%, #ffffff 100%)"}}
      />

      {/* Camada de fundo — lentas, transparentes */}
      <FloatingCloud layer="back"  variant="C" top="5%" duration={60} delay={0}  direction="right" />
      <FloatingCloud layer="back"  variant="A" top="28%" duration={55} delay={20} direction="left"  />
      <FloatingCloud layer="back"  variant="D" top="52%" duration={65} delay={10} direction="right" />
      <FloatingCloud layer="back"  variant="B" top="74%" duration={58} delay={32} direction="left"  />
      <FloatingCloud layer="back"  variant="C" top="88%" duration={62} delay={5}  direction="right" />

      {/* Camada do meio — velocidade e opacidade médias, com deriva vertical */}
      <FloatingCloud layer="mid"   variant="B" top="12%" duration={40} delay={8}  direction="right" floatVertical />
      <FloatingCloud layer="mid"   variant="D" top="38%" duration={44} delay={25} direction="left"  floatVertical />
      <FloatingCloud layer="mid"   variant="A" top="60%" duration={36} delay={14} direction="right" floatVertical />
      <FloatingCloud layer="mid"   variant="C" top="80%" duration={42} delay={3}  direction="left"  floatVertical />
      <FloatingCloud layer="mid"   variant="B" top="22%" duration={38} delay={36} direction="right" floatVertical />

      {/* Camada da frente — rápidas, mais opacas */}
      <FloatingCloud layer="front" variant="A" top="7%" duration={28} delay={6}  direction="left"  />
      <FloatingCloud layer="front" variant="D" top="30%" duration={24} delay={18} direction="right" />
      <FloatingCloud layer="front" variant="B" top="55%" duration={30} delay={0}  direction="left"  />
      <FloatingCloud layer="front" variant="C" top="70%" duration={26} delay={12} direction="right" />
      <FloatingCloud layer="front" variant="A" top="90%" duration={32} delay={22} direction="left"  />

      {/* Fade suave na base */}
      <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-white/50 to-transparent" />
    </div>
  )
}
