"use client"

import * as React from "react"
import { XIcon } from "lucide-react"

import { cn } from "@/lib/utils"

type DialogContextValue = {
  open: boolean
  setOpen: (open: boolean) => void
}

const DialogContext = React.createContext<DialogContextValue | null>(null)

function useDialog() {
  const context = React.useContext(DialogContext)
  if (!context) {
    throw new Error("useDialog must be used within a Dialog component")
  }
  return context
}

function Dialog({
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
    <DialogContext.Provider value={contextValue}>
      <div {...props}>{children}</div>
    </DialogContext.Provider>
  )
}

function DialogTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<"button">) {
  const { setOpen } = useDialog()

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

function DialogContent({
  className,
  children,
  showCloseButton = true,
  ...props
}: React.ComponentProps<"div"> & {
  showCloseButton?: boolean
}) {
  const { open, setOpen } = useDialog()
  const ref = React.useRef<HTMLDivElement>(null)

  // Handle click outside
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

  // Handle escape key
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
    <div className="modal modal-open">
      <div
        ref={ref}
        className={cn("modal-box", className)}
        onClick={(e) => e.stopPropagation()}
        {...props}
      >
        {children}
        {showCloseButton && (
          <button
            type="button"
            className="absolute btn btn-sm btn-circle btn-ghost right-4 top-4"
            onClick={() => setOpen(false)}
          >
            <XIcon className="h-4 w-4" />
          </button>
        )}
      </div>
      <form method="dialog" className="modal-backdrop">
        <button type="button" onClick={() => setOpen(false)}>close</button>
      </form>
    </div>
  )
}

function DialogHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("flex flex-col gap-2", className)}
      {...props}
    />
  )
}

function DialogFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("modal-action", className)}
      {...props}
    />
  )
}

function DialogTitle({
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

function DialogDescription({
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

function DialogClose({
  className,
  children,
  ...props
}: React.ComponentProps<"button">) {
  const { setOpen } = useDialog()

  return (
    <button
      type="button"
      onClick={() => setOpen(false)}
      className={cn("", className)}
      {...props}
    >
      {children}
    </button>
  )
}

export {
  Dialog,
  DialogClose,
  DialogHeader,
  DialogFooter,
  DialogTitle,
  DialogDescription,
  DialogContent,
  DialogTrigger,
}
