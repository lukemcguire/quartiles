import { AlertCircle, RotateCcw, Trophy } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Skeleton } from "@/components/ui/skeleton"
import {
  type GameSession,
  useGameStart,
  useGetHint,
  useSubmitGame,
  useValidateWord,
} from "@/hooks/useGame"
import { type FoundWord, FoundWordsList } from "./FoundWordsList"
import { GameBoard } from "./GameBoard"
import { GameInput } from "./GameInput"
import { GameStatus } from "./GameStatus"

const MAX_HINTS = 5

export function Game() {
  // Game session state
  const [gameSession, setGameSession] = useState<GameSession | null>(null)
  const [foundWords, setFoundWords] = useState<FoundWord[]>([])
  const [selectedTileIds, setSelectedTileIds] = useState<number[]>([])
  const [timeElapsed, setTimeElapsed] = useState(0)
  const [hintsUsed, setHintsUsed] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [showScoreAnimation, setShowScoreAnimation] = useState(false)
  const [showCompleteDialog, setShowCompleteDialog] = useState(false)

  // Mutations
  const gameStartMutation = useGameStart()
  const validateWordMutation = useValidateWord()
  const submitGameMutation = useSubmitGame()
  const getHintMutation = useGetHint()

  // Initialize game
  useEffect(() => {
    gameStartMutation.mutate(undefined, {
      onSuccess: (session) => {
        setGameSession(session)
        // Restore previous session if available
        if (session.previousResult) {
          // Could show previous results here
        }
      },
    })
  }, [gameStartMutation.mutate])

  // Timer
  useEffect(() => {
    if (!gameSession || showCompleteDialog) return

    const interval = setInterval(() => {
      setTimeElapsed((prev) => prev + 1000)
    }, 1000)

    return () => clearInterval(interval)
  }, [gameSession, showCompleteDialog])

  // Build current word from selected tiles
  const currentWord = useMemo(() => {
    if (!gameSession || selectedTileIds.length === 0) return ""

    return selectedTileIds
      .map((id) => gameSession.tiles.find((t) => t.id === id)?.letters || "")
      .join("")
  }, [gameSession, selectedTileIds])

  // Get used tile IDs
  const usedTileIds = useMemo(() => {
    const used = new Set<number>()
    foundWords.forEach((_fw) => {
      // For now, we don't track which tiles were used for each word
      // In a full implementation, you'd track this
    })
    return used
  }, [foundWords])

  // Handle tile click
  const handleTileClick = useCallback(
    (tileId: number) => {
      setErrorMessage(null)

      if (selectedTileIds.includes(tileId)) {
        // Deselect
        setSelectedTileIds((prev) => prev.filter((id) => id !== tileId))
      } else {
        // Select
        setSelectedTileIds((prev) => [...prev, tileId])
      }
    },
    [selectedTileIds],
  )

  // Clear selection
  const handleClear = useCallback(() => {
    setSelectedTileIds([])
    setErrorMessage(null)
  }, [])

  // Submit word
  const handleSubmit = useCallback(async () => {
    if (!gameSession || !currentWord) return

    setErrorMessage(null)

    try {
      const result = await validateWordMutation.mutateAsync({
        sessionId: gameSession.sessionId,
        word: currentWord,
      })

      if (result.isValid) {
        // Add to found words
        setFoundWords((prev) => [
          ...prev,
          {
            word: currentWord,
            points: result.points || 0,
            isQuartile: result.isQuartile || false,
          },
        ])

        // Clear selection
        setSelectedTileIds([])

        // Show score animation
        setShowScoreAnimation(true)
        setTimeout(() => setShowScoreAnimation(false), 200)

        // Check if solved
        if (result.isSolved) {
          // Auto-submit game
          await submitGameMutation.mutateAsync(gameSession.sessionId)
          setShowCompleteDialog(true)
        }
      } else {
        // Show error
        setErrorMessage(result.reason || "Invalid word")
      }
    } catch (error) {
      setErrorMessage("Failed to validate word. Please try again.")
      console.error("Validation error:", error)
    }
  }, [gameSession, currentWord, validateWordMutation, submitGameMutation])

  // Request hint
  const handleRequestHint = useCallback(async () => {
    if (!gameSession || hintsUsed >= MAX_HINTS) return

    try {
      const hint = await getHintMutation.mutateAsync(gameSession.sessionId)
      setHintsUsed(hint.hintNumber)
      setErrorMessage(`Hint: ${hint.definition || "No definition available"}`)
    } catch (error) {
      setErrorMessage("Failed to get hint. Please try again.")
      console.error("Hint error:", error)
    }
  }, [gameSession, hintsUsed, getHintMutation])

  // Calculate current score
  const currentScore = useMemo(() => {
    return foundWords.reduce((sum, fw) => sum + fw.points, 0)
  }, [foundWords])

  // Loading state
  if (gameStartMutation.isPending) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[500px] gap-6">
        <Skeleton className="h-[400px] w-[400px] rounded-2xl" />
        <Skeleton className="h-12 w-64" />
      </div>
    )
  }

  // Error state
  if (gameStartMutation.error) {
    return (
      <Alert variant="destructive" className="max-w-md mx-auto">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load game. Please refresh the page to try again.
        </AlertDescription>
      </Alert>
    )
  }

  // No game session
  if (!gameSession) {
    return null
  }

  const canSubmit = currentWord.length >= 2 && !validateWordMutation.isPending

  return (
    <div className="flex flex-col items-center gap-6 w-full">
      {/* Status Bar */}
      <GameStatus
        timeElapsed={timeElapsed}
        hintsUsed={hintsUsed}
        maxHints={MAX_HINTS}
        onRequestHint={handleRequestHint}
        isHintDisabled={hintsUsed >= MAX_HINTS || showCompleteDialog}
        isRequestingHint={getHintMutation.isPending}
        className="w-full max-w-2xl"
      />

      {/* Main Game Area */}
      <div className="flex flex-col lg:flex-row gap-6 w-full max-w-6xl items-start">
        {/* Left: Game Board and Input */}
        <div className="flex-1 flex flex-col items-center gap-6 w-full">
          <GameBoard
            tiles={gameSession.tiles}
            selectedTileIds={selectedTileIds}
            usedTileIds={usedTileIds}
            onTileClick={handleTileClick}
            disabled={showCompleteDialog}
          />

          <GameInput
            currentWord={currentWord}
            canSubmit={canSubmit}
            isSubmitting={validateWordMutation.isPending}
            onClear={handleClear}
            onSubmit={handleSubmit}
            score={currentScore}
            showScoreAnimation={showScoreAnimation}
            errorMessage={errorMessage}
          />
        </div>

        {/* Right: Found Words */}
        <div className="w-full lg:w-80">
          <FoundWordsList words={foundWords} />
        </div>
      </div>

      {/* Complete Dialog */}
      <Dialog open={showCompleteDialog} onOpenChange={setShowCompleteDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Trophy className="h-6 w-6 text-warning" />
              Puzzle Complete!
            </DialogTitle>
            <DialogDescription>
              Congratulations! You found all the quartiles.
            </DialogDescription>
          </DialogHeader>

          {submitGameMutation.data && (
            <div className="space-y-4 py-4">
              <div className="text-center">
                <div className="text-sm text-muted-foreground">Final Score</div>
                <div className="text-4xl font-bold">
                  {submitGameMutation.data.finalScore}
                </div>
              </div>

              {submitGameMutation.data.solveTimeMs && (
                <div className="text-center">
                  <div className="text-sm text-muted-foreground">Time</div>
                  <div className="text-xl font-semibold">
                    {Math.floor(submitGameMutation.data.solveTimeMs / 1000)}s
                  </div>
                </div>
              )}

              {submitGameMutation.data.leaderboardRank && (
                <div className="text-center">
                  <div className="text-sm text-muted-foreground">
                    Leaderboard Rank
                  </div>
                  <div className="text-xl font-semibold text-primary">
                    #{submitGameMutation.data.leaderboardRank}
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button onClick={() => window.location.reload()} variant="outline">
              <RotateCcw className="mr-2 h-4 w-4" />
              Play Again
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
