import * as React from "react"
import { cn } from "@/lib/utils"

const Skeleton = React.memo(function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse motion-reduce:animate-none rounded-md bg-gray-200 dark:bg-lia-bg-elevated", className)}
      {...props}
    />
  )
})
Skeleton.displayName = 'Skeleton'

export { Skeleton }
