import { Check, Eraser } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export interface GameInputProps {
  currentWord: string
  canSubmit: boolean
  isSubmitting: boolean
  onClear: () => void
  onSubmit: () => void
  score: number
  showScoreAnimation?: boolean
  errorMessage?: string | null
}

export function GameInput({
  currentWord,
  canSubmit,
  isSubmitting,
  onClear,
  onSubmit,
  score,
  showScoreAnimation,
  errorMessage,
}: GameInputProps) {
  return (
    <div className="space-y-4 w-full max-w-md">
      {/* Score Display */}
      <div className="text-center">
        <div className="text-sm text-muted-foreground mb-1">Score</div>
        <div
          data-testid="score-value"
          className={cn(
            "text-4xl font-bold transition-all",
            showScoreAnimation && "animate-count-up",
          )}
        >
          {score}
        </div>
      </div>

      {/* Current Word Display */}
      <div className="bg-base-100 rounded-xl p-6 card-organic">
        <div className="text-center">
          <div className="text-sm text-muted-foreground mb-2">Current Word</div>
          <div
            data-testid="current-word"
            className={cn(
              "min-h-[60px] flex items-center justify-center text-3xl font-bold tracking-wider",
              currentWord ? "text-base-content" : "text-muted-foreground",
              errorMessage && "animate-shake",
            )}
          >
            {currentWord || (
              <span className="text-lg">Select tiles to form a word</span>
            )}
          </div>
        </div>

        {/* Error Message */}
        {errorMessage && (
          <div className="mt-3 text-center text-sm text-destructive animate-fade-in">
            {errorMessage}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3">
        <Button
          type="button"
          variant="outline"
          size="lg"
          onClick={onClear}
          disabled={!currentWord || isSubmitting}
          className="flex-1 btn-organic"
        >
          <Eraser className="mr-2 h-4 w-4" />
          Clear
        </Button>
        <Button
          type="button"
          size="lg"
          onClick={onSubmit}
          disabled={!canSubmit || isSubmitting}
          className={cn(
            "flex-1 btn-organic",
            canSubmit && "animate-pulse-glow",
          )}
        >
          <Check className="mr-2 h-4 w-4" />
          Submit
        </Button>
      </div>
    </div>
  )
}
