import { AlertCircle, RotateCcw, Trophy } from "lucide-react"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  type GameSession,
  useGameStart,
  useGetHint,
  useSubmitGame,
  useValidateWord,
} from "@/hooks/useGame"
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation"
import { type FoundWord, FoundWordsList } from "./FoundWordsList"
import { GameBoard } from "./GameBoard"
import { GameInput } from "./GameInput"
import { GameStatus } from "./GameStatus"

// localStorage persistence
const STORAGE_KEY = "quartiles_game_session"
const SESSION_VALIDITY_MS = 24 * 60 * 60 * 1000 // 24 hours

interface StoredGameState {
  sessionId: string
  timestamp: number
  tiles: Array<{ id: number; letters: string }>
  foundWords: FoundWord[]
  selectedTileIds: number[]
  timeElapsed: number
  hintsUsed: number
}

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

  // localStorage: Save state on changes
  useEffect(() => {
    if (gameSession && !showCompleteDialog) {
      const state: StoredGameState = {
        sessionId: gameSession.sessionId,
        timestamp: Date.now(),
        tiles: gameSession.tiles,
        foundWords,
        selectedTileIds,
        timeElapsed,
        hintsUsed,
      }
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
      } catch (e) {
        console.warn("Failed to save game state:", e)
      }
    }
  }, [
    gameSession,
    foundWords,
    selectedTileIds,
    timeElapsed,
    hintsUsed,
    showCompleteDialog,
  ])

  // localStorage: Restore on mount
  useEffect(() => {
    if (!gameSession) return

    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return

    try {
      const parsed = JSON.parse(stored) as StoredGameState
      const age = Date.now() - parsed.timestamp

      // Only restore if < 24 hours and same session
      if (
        age < SESSION_VALIDITY_MS &&
        parsed.sessionId === gameSession.sessionId
      ) {
        setFoundWords(parsed.foundWords)
        setSelectedTileIds(parsed.selectedTileIds)
        setTimeElapsed(parsed.timeElapsed)
        setHintsUsed(parsed.hintsUsed)
      } else {
        // Clear stale or mismatched session
        localStorage.removeItem(STORAGE_KEY)
      }
    } catch (e) {
      console.warn("Failed to restore game state:", e)
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [gameSession])

  // localStorage: Clear on completion
  useEffect(() => {
    if (showCompleteDialog) {
      localStorage.removeItem(STORAGE_KEY)
    }
  }, [showCompleteDialog])

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

  // Keyboard navigation (must be after handleClear and handleSubmit are defined)
  const { focusedIndex, keyHandlers } = useKeyboardNavigation({
    tileCount: gameSession?.tiles.length ?? 20,
    columns: 4,
    onTileSelect: (index) => {
      if (gameSession) {
        handleTileClick(gameSession.tiles[index].id)
      }
    },
    onClear: handleClear,
    onSubmit: handleSubmit,
    disabled: showCompleteDialog || !gameSession,
  })

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
        <div className="skeleton h-[400px] w-[400px] rounded-2xl" />
        <div className="skeleton h-12 w-64" />
      </div>
    )
  }

  // Error state
  if (gameStartMutation.error) {
    return (
      <div className="alert alert-error max-w-md mx-auto shadow-lg">
        <AlertCircle className="h-4 w-4" />
        <span>Failed to load game. Please refresh the page to try again.</span>
      </div>
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
            focusedIndex={focusedIndex}
            onKeyDown={keyHandlers.onKeyDown}
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
      <dialog className={`modal ${showCompleteDialog ? "modal-open" : ""}`}>
        <div className="modal-box">
          <h3 className="font-bold text-lg flex items-center gap-2">
            <Trophy className="h-6 w-6 text-warning" />
            Puzzle Complete!
          </h3>
          <p className="py-4">Congratulations! You found all the quartiles.</p>

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

          <div className="modal-action">
            <button
              type="button"
              className="btn btn-outline"
              onClick={() => window.location.reload()}
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Play Again
            </button>
          </div>
        </div>
        <form method="dialog" className="modal-backdrop">
          <button type="button" onClick={() => setShowCompleteDialog(false)}>
            close
          </button>
        </form>
      </dialog>
    </div>
  )
}
