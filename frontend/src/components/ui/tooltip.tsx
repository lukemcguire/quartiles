"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

type TooltipContextValue = {
  open: boolean
  setOpen: (open: boolean) => void
}

const TooltipContext = React.createContext<TooltipContextValue | null>(null)

function useTooltip() {
  const context = React.useContext(TooltipContext)
  if (!context) {
    throw new Error("useTooltip must be used within a Tooltip")
  }
  return context
}

function TooltipProvider({
  delayDuration = 0,
  children,
  ...props
}: React.ComponentProps<"div"> & {
  delayDuration?: number
}) {
  return <div {...props}>{children}</div>
}

function Tooltip({
  children,
  open: controlledOpen,
  onOpenChange,
  defaultOpen = false,
  ...props
}: React.ComponentProps<"div"> & {
  open?: boolean
  onOpenChange?: (open: boolean) => void
  defaultOpen?: boolean
}) {
  const [uncontrolledOpen, setUncontrolledOpen] = React.useState(defaultOpen)

  const open = controlledOpen ?? uncontrolledOpen
  const setOpen = React.useCallback(
    (value: boolean | ((value: boolean) => boolean)) => {
      const openState = typeof value === "function" ? value(open) : value
      if (controlledOpen === undefined) {
        setUncontrolledOpen(openState)
      }
      onOpenChange?.(openState)
    },
    [controlledOpen, onOpenChange, open]
  )

  const contextValue = React.useMemo(
    () => ({ open, setOpen }),
    [open, setOpen]
  )

  return (
    <TooltipContext.Provider value={contextValue}>
      <div
        className="tooltip-wrap relative inline-block"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        {...props}
      >
        {children}
      </div>
    </TooltipContext.Provider>
  )
}

function TooltipTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div className={cn("", className)} {...props}>
      {children}
    </div>
  )
}

function TooltipContent({
  className,
  children,
  side = "top",
  sideOffset = 0,
  ...props
}: React.ComponentProps<"div"> & {
  side?: "top" | "right" | "bottom" | "left"
  sideOffset?: number
}) {
  const { open } = useTooltip()

  if (!open) return null

  return (
    <div
      className={cn(
        "tooltip tooltip-open",
        side === "top" && "tooltip-top",
        side === "bottom" && "tooltip-bottom",
        side === "left" && "tooltip-left",
        side === "right" && "tooltip-right",
        className
      )}
      style={{
        marginTop: sideOffset ? `${sideOffset}px` : undefined,
      }}
      {...props}
    >
      {children}
    </div>
  )
}

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider }
