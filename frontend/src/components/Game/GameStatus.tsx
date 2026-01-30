import { Clock, Lightbulb, Trophy } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export interface GameStatusProps {
  timeElapsed: number
  hintsUsed: number
  maxHints: number
  onRequestHint?: () => void
  isHintDisabled?: boolean
  isRequestingHint?: boolean
  className?: string
}

export function GameStatus({
  timeElapsed,
  hintsUsed,
  maxHints,
  onRequestHint,
  isHintDisabled,
  isRequestingHint = false,
  className,
}: GameStatusProps) {
  const formatTime = (ms: number): string => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`
  }

  return (
    <div className={cn("flex items-center justify-between gap-4", className)}>
      {/* Time */}
      <div className="flex items-center gap-2 bg-base-100 px-4 py-2 rounded-lg card-organic">
        <Clock className="h-4 w-4 text-muted-foreground" />
        <span className="font-mono font-semibold" data-testid="timer">
          {formatTime(timeElapsed)}
        </span>
      </div>

      {/* Hints */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-2 bg-base-100 px-4 py-2 rounded-lg card-organic">
          <Lightbulb className="h-4 w-4 text-muted-foreground" />
          <span className="font-semibold">
            {hintsUsed}/{maxHints}
          </span>
        </div>

        {onRequestHint && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onRequestHint}
            disabled={isHintDisabled || isRequestingHint}
            className="btn-organic"
          >
            <Trophy className="h-4 w-4 mr-1" />
            Hint
          </Button>
        )}
      </div>
    </div>
  )
}
