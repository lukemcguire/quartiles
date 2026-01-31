"use client"

import * as React from "react"
import { XIcon } from "lucide-react"

import { cn } from "@/lib/utils"

type SheetContextValue = {
  open: boolean
  setOpen: (open: boolean) => void
}

const SheetContext = React.createContext<SheetContextValue | null>(null)

function useSheet() {
  const context = React.useContext(SheetContext)
  if (!context) {
    throw new Error("useSheet must be used within a Sheet")
  }
  return context
}

function Sheet({
  open: controlledOpen,
  onOpenChange,
  defaultOpen = false,
  children,
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
    <SheetContext.Provider value={contextValue}>
      <div {...props}>{children}</div>
    </SheetContext.Provider>
  )
}

function SheetTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<"button">) {
  const { setOpen } = useSheet()

  return (
    <button
      type="button"
      onClick={() => setOpen(true)}
      className={cn("", className)}
      {...props}
    >
      {children}
    </button>
  )
}

function SheetContent({
  className,
  children,
  side = "right",
  ...props
}: React.ComponentProps<"div"> & {
  side?: "top" | "right" | "bottom" | "left"
}) {
  const { open, setOpen } = useSheet()
  const ref = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener("mousedown", handleClickOutside)
      return () => {
        document.removeEventListener("mousedown", handleClickOutside)
      }
    }
  }, [open, setOpen])

  React.useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false)
      }
    }

    if (open) {
      document.addEventListener("keydown", handleEscape)
      return () => {
        document.removeEventListener("keydown", handleEscape)
      }
    }
  }, [open, setOpen])

  if (!open) return null

  return (
    <>
      <div
        className="modal modal-open"
        style={{
          alignItems: side === "top" || side === "bottom" ? "center" : "center",
          justifyContent: side === "left" ? "flex-start" : side === "right" ? "flex-end" : "center",
        }}
      >
        <div
          ref={ref}
          className={cn(
            "modal-box",
            side === "left" && "rounded-r-lg rounded-l-none",
            side === "right" && "rounded-l-lg rounded-r-none",
            side === "top" && "rounded-b-lg rounded-t-none",
            side === "bottom" && "rounded-t-lg rounded-b-none",
            className
          )}
          onClick={(e) => e.stopPropagation()}
          {...props}
        >
          <button
            type="button"
            className="absolute btn btn-sm btn-circle btn-ghost right-4 top-4"
            onClick={() => setOpen(false)}
          >
            <XIcon className="h-4 w-4" />
          </button>
          {children}
        </div>
      </div>
      <div
        className="modal-backdrop"
        onClick={() => setOpen(false)}
      />
    </>
  )
}

function SheetHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("flex flex-col gap-2", className)}
      {...props}
    />
  )
}

function SheetFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("modal-action", className)}
      {...props}
    />
  )
}

function SheetTitle({
  className,
  ...props
}: React.ComponentProps<"h3">) {
  return (
    <h3
      className={cn("font-bold text-lg", className)}
      {...props}
    />
  )
}

function SheetDescription({
  className,
  ...props
}: React.ComponentProps<"p">) {
  return (
    <p
      className={cn("text-base-content/70 text-sm", className)}
      {...props}
    />
  )
}

export {
  Sheet,
  SheetTrigger,
  SheetContent,
  SheetHeader,
  SheetFooter,
  SheetTitle,
  SheetDescription,
}
