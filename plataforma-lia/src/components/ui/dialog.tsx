"use client"

import * as React from "react"
import * as DialogPrimitive from "@radix-ui/react-dialog"
import { X } from "lucide-react"

import { cn } from "@/lib/utils"

const Dialog = DialogPrimitive.Root

const DialogTrigger = DialogPrimitive.Trigger

const DialogPortal = DialogPrimitive.Portal

const DialogClose = DialogPrimitive.Close

const DialogOverlay = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Overlay>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Overlay>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Overlay
    ref={ref}
    className={cn(
 "fixed inset-0 z-50 bg-black/30 backdrop-blur-[1px] data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0",
      className
    )}
    {...props}
  />
))
DialogOverlay.displayName = DialogPrimitive.Overlay.displayName

const DialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content>
>(({ className, children, style, ...props }, ref) => (
  <DialogPortal container={typeof document !== 'undefined' ? document.body : undefined}>
    <div className="fixed inset-0 z-backdrop flex items-center justify-center pointer-events-none">
      <DialogOverlay className="pointer-events-auto" />
      <DialogPrimitive.Content
        ref={ref}
        className={cn(
 "relative z-modal grid w-full max-w-lg gap-4 border border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary p-6 rounded-xl duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 pointer-events-auto",
          className
        )}
        style={style}
        {...props}
      >
        {children}
        <DialogPrimitive.Close className="absolute right-4 top-4 rounded-xl p-1 text-lia-text-secondary transition-colors motion-reduce:transition-none hover:text-lia-text-primary hover:bg-lia-interactive-hover focus:outline-none focus:ring-1 focus:ring-lia-border-medium disabled:pointer-events-none data-[state=open]:bg-lia-bg-tertiary data-[state=open]:text-lia-text-primary">
          <X className="h-4 w-4" />
          <span className="sr-only">Close</span>
        </DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </div>
  </DialogPortal>
))
DialogContent.displayName = DialogPrimitive.Content.displayName

interface DraggableDialogContentProps extends React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> {
  onPositionReset?: () => void
}

const DraggableDialogContent = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Content>,
  DraggableDialogContentProps
>(({ className, children, style, ...props }, ref) => {
  const [position, setPosition] = React.useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = React.useState(false)
  const dragStartPos = React.useRef({ x: 0, y: 0 })
  const dialogRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    setPosition({ x: 0, y: 0 })
  }, [])

  const handleMouseDown = (e: React.MouseEvent) => {
    if ((e.target as HTMLElement).closest('[data-dialog-close]') || 
        (e.target as HTMLElement).closest('button')) {
      return
    }
    setIsDragging(true)
    dragStartPos.current = {
      x: e.clientX - position.x,
      y: e.clientY - position.y
    }
    e.preventDefault()
  }

  React.useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return
      setPosition({
        x: e.clientX - dragStartPos.current.x,
        y: e.clientY - dragStartPos.current.y
      })
    }

    const handleMouseUp = () => {
      setIsDragging(false)
    }

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging])

  return (
    <DialogPortal container={typeof document !== 'undefined' ? document.body : undefined}>
      <div className="fixed inset-0 z-backdrop flex items-center justify-center pointer-events-none">
        <DialogOverlay className="pointer-events-auto" />
        <DialogPrimitive.Content
          ref={(node) => {
            if (typeof ref === 'function') ref(node)
            else if (ref) ref.current = node
            dialogRef.current = node
          }}
          className={cn(
 "relative z-modal grid w-full max-w-lg gap-4 border border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary p-6 rounded-xl duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 pointer-events-auto",
            className
          )}
          style={{...style,
            transform: `translate(${position.x}px, ${position.y}px)`}}
          {...props}
        >
          <div
            className="absolute inset-x-0 top-0 h-12 cursor-move rounded-t-lg z-[1]"
            onMouseDown={handleMouseDown}
          />
          {children}
          <DialogPrimitive.Close className="absolute right-4 top-4 rounded-xl p-1 text-lia-text-secondary transition-colors motion-reduce:transition-none hover:text-lia-text-primary hover:bg-lia-interactive-hover focus:outline-none focus:ring-1 focus:ring-lia-border-medium disabled:pointer-events-none data-[state=open]:bg-lia-bg-tertiary data-[state=open]:text-lia-text-primary z-10" data-dialog-close>
            <X className="h-4 w-4" />
            <span className="sr-only">Close</span>
          </DialogPrimitive.Close>
        </DialogPrimitive.Content>
      </div>
    </DialogPortal>
  )
})
DraggableDialogContent.displayName = "DraggableDialogContent"

const DialogHeader = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
 "flex flex-col space-y-1.5 text-center sm:text-left",
      className
    )}
    {...props}
  />
)
DialogHeader.displayName = "DialogHeader"

const DialogFooter = ({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
 "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2",
      className
    )}
    {...props}
  />
)
DialogFooter.displayName = "DialogFooter"

const DialogTitle = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Title>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Title>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Title
    ref={ref}
    className={cn(
 "text-xs font-semibold leading-none tracking-tight",
      className
    )}
    {...props}
  />
))
DialogTitle.displayName = DialogPrimitive.Title.displayName

const DialogDescription = React.forwardRef<
  React.ElementRef<typeof DialogPrimitive.Description>,
  React.ComponentPropsWithoutRef<typeof DialogPrimitive.Description>
>(({ className, ...props }, ref) => (
  <DialogPrimitive.Description
    ref={ref}
    className={cn("text-xs text-lia-text-secondary", className)}
    {...props}
  />
))
DialogDescription.displayName = DialogPrimitive.Description.displayName

export {
  Dialog,
  DialogPortal,
  DialogOverlay,
  DialogClose,
  DialogTrigger,
  DialogContent,
  DraggableDialogContent,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
}
