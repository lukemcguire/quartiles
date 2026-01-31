"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

type TabsContextValue = {
  value: string
  onValueChange: (value: string) => void
}

const TabsContext = React.createContext<TabsContextValue | null>(null)

function useTabs() {
  const context = React.useContext(TabsContext)
  if (!context) {
    throw new Error("useTabs must be used within a Tabs component")
  }
  return context
}

function Tabs({
  defaultValue,
  value: controlledValue,
  onValueChange,
  className,
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
    () => ({ value, onValueChange: setValue }),
    [value, setValue]
  )

  return (
    <TabsContext.Provider value={contextValue}>
      <div className={cn("flex flex-col gap-2", className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  )
}

function TabsList({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      role="tablist"
      className={cn("tabs tabs-boxed bg-base-200", className)}
      {...props}
    />
  )
}

function TabsTrigger({
  value: triggerValue,
  className,
  children,
  ...props
}: React.ComponentProps<"button"> & {
  value: string
}) {
  const { value, onValueChange } = useTabs()

  return (
    <button
      role="tab"
      type="button"
      aria-selected={value === triggerValue}
      className={cn("tab", value === triggerValue && "tab-active", className)}
      onClick={() => onValueChange(triggerValue)}
      {...props}
    >
      {children}
    </button>
  )
}

function TabsContent({
  value: contentValue,
  className,
  children,
  ...props
}: React.ComponentProps<"div"> & {
  value: string
}) {
  const { value } = useTabs()

  if (value !== contentValue) {
    return null
  }

  return (
    <div
      role="tabpanel"
      className={cn("", className)}
      {...props}
    >
      {children}
    </div>
  )
}

export { Tabs, TabsList, TabsTrigger, TabsContent }
