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
      {/* Score Display - using output for accessibility */}
      <output className="block text-center">
        <div className="text-sm text-muted-foreground mb-1" id="score-label">
          Score
        </div>
        <div
          data-testid="score-value"
          className={cn(
            "text-4xl font-bold transition-all",
            showScoreAnimation && "animate-count-up",
          )}
        >
          {score} / 100
        </div>
      </output>

      {/* Current Word Display */}
      <div className="bg-base-100 rounded-xl p-6 card-organic">
        <div className="text-center">
          <div
            className="text-sm text-muted-foreground mb-2"
            id="current-word-label"
          >
            Current Word
          </div>
          <output
            data-testid="current-word"
            htmlFor="tile-grid"
            className={cn(
              "min-h-[60px] flex items-center justify-center text-3xl font-bold tracking-wider",
              currentWord ? "text-base-content" : "text-muted-foreground",
              errorMessage && "animate-shake",
            )}
          >
            {currentWord || (
              <span className="text-lg">Select tiles to form a word</span>
            )}
          </output>
        </div>

        {/* Error Message - with aria-live for screen readers */}
        {errorMessage && (
          <div
            className="mt-3 text-center text-sm text-destructive animate-fade-in"
            role="alert"
            aria-live="assertive"
          >
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
          aria-label="Clear selected tiles"
        >
          <Eraser className="mr-2 h-4 w-4" aria-hidden="true" />
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
          aria-label={canSubmit ? `Submit word: ${currentWord}` : "Submit word"}
        >
          <Check className="mr-2 h-4 w-4" aria-hidden="true" />
          Submit
        </Button>
      </div>
    </div>
  )
}
