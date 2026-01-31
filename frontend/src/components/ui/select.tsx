"use client"

import * as React from "react"
import { ChevronDownIcon } from "lucide-react"

import { cn } from "@/lib/utils"

type SelectContextValue = {
  value: string
  onValueChange: (value: string) => void
  open: boolean
  setOpen: (open: boolean) => void
}

const SelectContext = React.createContext<SelectContextValue | null>(null)

function useSelect() {
  const context = React.useContext(SelectContext)
  if (!context) {
    throw new Error("useSelect must be used within a Select component")
  }
  return context
}

function Select({
  defaultValue,
  value: controlledValue,
  onValueChange,
  children,
  ...props
}: React.ComponentProps<"div"> & {
  defaultValue?: string
  value?: string
  onValueChange?: (value: string) => void
}) {
  const [uncontrolledValue, setUncontrolledValue] = React.useState(
    defaultValue || ""
  )
  const [open, setOpen] = React.useState(false)

  const value = controlledValue ?? uncontrolledValue
  const setValue = React.useCallback(
    (newValue: string) => {
      if (controlledValue === undefined) {
        setUncontrolledValue(newValue)
      }
      onValueChange?.(newValue)
    },
    [controlledValue, onValueChange]
  )

  const contextValue = React.useMemo(
    () => ({ value, onValueChange: setValue, open, setOpen }),
    [value, setValue, open, setOpen]
  )

  return (
    <SelectContext.Provider value={contextValue}>
      <div {...props}>{children}</div>
    </SelectContext.Provider>
  )
}

function SelectTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<"button">) {
  const { setOpen, open } = useSelect()

  return (
    <button
      type="button"
      onClick={() => setOpen(!open)}
      className={cn(
        "select select-bordered flex items-center justify-between gap-2",
        className
      )}
      {...props}
    >
      {children}
      <ChevronDownIcon className="w-4 h-4 opacity-50" />
    </button>
  )
}

function SelectValue({
  placeholder,
  className,
  ...props
}: React.ComponentProps<"span"> & {
  placeholder?: string
}) {
  const { value } = useSelect()

  return (
    <span className={cn("block truncate", className)} {...props}>
      {value || placeholder}
    </span>
  )
}

function SelectContent({
  className,
  children,
  ...props
}: React.ComponentProps<"ul">) {
  const { open, setOpen } = useSelect()
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
        "dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow-sm border border-base-300 absolute top-full left-0 mt-1",
        className
      )}
      {...props}
    >
      {children}
    </ul>
  )
}

function SelectItem({
  value: itemValue,
  className,
  children,
  onClick,
  ...props
}: React.ComponentProps<"button"> & {
  value: string
}) {
  const { value, onValueChange, setOpen } = useSelect()

  return (
    <li>
      <button
        type="button"
        onClick={(e) => {
          onClick?.(e)
          onValueChange(itemValue)
          setOpen(false)
        }}
        className={cn(
          "w-full text-left px-4 py-2 rounded hover:bg-base-200",
          value === itemValue && "bg-base-200",
          className
        )}
        {...props}
      >
        {children}
      </button>
    </li>
  )
}

function SelectLabel({
  className,
  ...props
}: React.ComponentProps<"li">) {
  return (
    <li className={cn("px-4 py-2 text-sm opacity-70", className)} {...props} />
  )
}

function SelectSeparator({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <li>
      <div className={cn("divider my-0", className)} {...props} />
    </li>
  )
}

function SelectGroup({
  className,
  ...props
}: React.ComponentProps<"ul">) {
  return <ul className={cn("", className)} {...props} />
}

export {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectGroup,
}
