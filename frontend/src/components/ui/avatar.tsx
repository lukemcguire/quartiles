import * as React from "react"

import { cn } from "@/lib/utils"

function Avatar({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("avatar", className)}
      {...props}
    />
  )
}

function AvatarImage({
  className,
  ...props
}: React.ComponentProps<"img">) {
  return (
    <div className="mask mask-squircle">
      <img
        className={cn("w-full h-full object-cover", className)}
        {...props}
      />
    </div>
  )
}

function AvatarFallback({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("bg-neutral text-neutral-content rounded-full", className)}
      {...props}
    />
  )
}

export { Avatar, AvatarImage, AvatarFallback }
