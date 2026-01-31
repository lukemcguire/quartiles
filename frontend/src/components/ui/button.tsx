import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "btn",
  {
    variants: {
      variant: {
        default: "btn-primary",
        destructive: "btn-error",
        outline: "btn-outline",
        secondary: "btn-secondary",
        ghost: "btn-ghost",
        link: "btn-link",
      },
      size: {
        default: "",
        sm: "btn-sm",
        lg: "btn-lg",
        icon: "btn-circle",
        "icon-sm": "btn-circle btn-sm",
        "icon-lg": "btn-circle btn-lg",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant,
  size,
  ...props
}: React.ComponentProps<"button"> &
  VariantProps<typeof buttonVariants>) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  )
}

export { Button, buttonVariants }
