import * as React from "react"

import { cn } from "@/lib/utils"

function Separator({
  className,
  orientation = "horizontal",
  ...props
}: React.ComponentProps<"div"> & { orientation?: "horizontal" | "vertical" }) {
  return (
    <div
      role="separator"
      aria-orientation={orientation}
      className={cn(
        "divider",
        orientation === "vertical" ? "divider-vertical" : "divider-horizontal",
        className
      )}
      {...props}
    />
  )
}

export { Separator }
