"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

type DropdownMenuContextValue = {
  open: boolean
  setOpen: (open: boolean) => void
}

const DropdownMenuContext = React.createContext<DropdownMenuContextValue | null>(null)

function useDropdownMenu() {
  const context = React.useContext(DropdownMenuContext)
  if (!context) {
    throw new Error("useDropdownMenu must be used within a DropdownMenu")
  }
  return context
}

function DropdownMenu({
  children,
  open: controlledOpen,
  onOpenChange,
  ...props
}: React.ComponentProps<"div"> & {
  open?: boolean
  onOpenChange?: (open: boolean) => void
}) {
  const [uncontrolledOpen, setUncontrolledOpen] = React.useState(false)

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
    <DropdownMenuContext.Provider value={contextValue}>
      <div {...props}>{children}</div>
    </DropdownMenuContext.Provider>
  )
}

function DropdownMenuTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<"button">) {
  const { setOpen, open } = useDropdownMenu()

  return (
    <button
      type="button"
      onClick={() => setOpen(!open)}
      className={cn("", className)}
      {...props}
    >
      {children}
    </button>
  )
}

function DropdownMenuContent({
  className,
  children,
  align = "center",
  sideOffset = 4,
  ...props
}: React.ComponentProps<"ul"> & {
  align?: "start" | "center" | "end"
  sideOffset?: number
}) {
  const { open, setOpen } = useDropdownMenu()
  const ref = React.useRef<HTMLUListElement>(null)

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

  if (!open) return null

  return (
    <ul
      ref={ref}
      className={cn(
        "dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow-sm border border-base-300",
        align === "start" && "dropdown-menu-left",
        align === "end" && "dropdown-menu-right",
        className
      )}
      style={{ marginTop: `${sideOffset}px` }}
      {...props}
    >
      {children}
    </ul>
  )
}

function DropdownMenuItem({
  className,
  children,
  variant = "default",
  onClick,
  ...props
}: React.ComponentProps<"button"> & {
  variant?: "default" | "destructive"
}) {
  const { setOpen } = useDropdownMenu()

  return (
    <li>
      <button
        type="button"
        onClick={(e) => {
          onClick?.(e)
          setOpen(false)
        }}
        className={cn(
          "w-full text-left px-4 py-2 rounded hover:bg-base-200",
          variant === "destructive" && "text-error hover:bg-error/10",
          className
        )}
        {...props}
      >
        {children}
      </button>
    </li>
  )
}

function DropdownMenuLabel({
  className,
  inset,
  ...props
}: React.ComponentProps<"div"> & { inset?: boolean }) {
  return (
    <div className={cn("px-4 py-2 text-sm font-medium", inset && "pl-8", className)} {...props} />
  )
}

function DropdownMenuSeparator({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <li>
      <div className={cn("divider my-1", className)} {...props} />
    </li>
  )
}

function DropdownMenuGroup({
  className,
  ...props
}: React.ComponentProps<"ul">) {
  return <ul className={cn("", className)} {...props} />
}

function DropdownMenuShortcut({
  className,
  ...props
}: React.ComponentProps<"span">) {
  return (
    <span className={cn("ml-auto text-xs opacity-70", className)} {...props} />
  )
}

export {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuGroup,
  DropdownMenuShortcut,
}
