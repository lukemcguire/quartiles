import { cn } from "@/lib/utils"

export interface TileProps {
  id: number
  letters: string
  isSelected: boolean
  isUsed?: boolean
  onClick: () => void
  disabled?: boolean
}

export function Tile({
  letters,
  isSelected,
  isUsed,
  onClick,
  disabled,
}: TileProps) {
  const hasMultipleLetters = letters.length > 1

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      data-testid="tile"
      className={cn(
        // Base styles
        "relative flex h-full w-full items-center justify-center rounded-lg font-semibold transition-all duration-200",
        // Organic theme styles
        "tile-button interactive",
        // Size and spacing
        "min-h-[80px] min-w-[80px] sm:min-h-[90px] sm:min-w-[90px] md:min-h-[100px] md:min-w-[100px]",
        // Text styling
        hasMultipleLetters
          ? "text-lg sm:text-xl"
          : "text-2xl sm:text-3xl md:text-4xl",
        // Colors based on state
        isSelected
          ? "bg-primary text-primary-foreground tile-selected animate-selection-ring"
          : "bg-base-100 text-base-content hover:bg-base-200",
        isUsed && "opacity-50",
        // Disabled state
        disabled && "cursor-not-allowed opacity-50",
        // Float animation for idle tiles
        !isSelected && !disabled && "animate-float pause-on-hover",
      )}
      aria-label={`Tile: ${letters}`}
      aria-pressed={isSelected}
    >
      {hasMultipleLetters ? (
        <span className="flex flex-col items-center leading-tight">
          {letters.split("").map((letter, index) => (
            <span key={index} className="text-[0.6em]">
              {letter}
            </span>
          ))}
        </span>
      ) : (
        <span>{letters}</span>
      )}
    </button>
  )
}
