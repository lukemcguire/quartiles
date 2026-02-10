import { Clock, TrendingUp, Trophy } from "lucide-react"
import { useEffect, useState } from "react"
import { cn } from "@/lib/utils"
import { formatCountdown, getTimeUntilNextPuzzle } from "@/utils/timezone"

export interface AlreadyPlayedProps {
  finalScore: number
  solveTimeMs?: number | null
  wordsFound: string[]
  leaderboardRank?: number | null
  className?: string
}

export function AlreadyPlayed({
  finalScore,
  solveTimeMs,
  wordsFound,
  leaderboardRank,
  className,
}: AlreadyPlayedProps) {
  const [timeRemaining, setTimeRemaining] = useState(getTimeUntilNextPuzzle())

  useEffect(() => {
    const interval = setInterval(
      () => setTimeRemaining(getTimeUntilNextPuzzle()),
      1000,
    )
    return () => clearInterval(interval)
  }, [])

  const formatSolveTime = (ms: number): string => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`
  }

  return (
    <div
      className={cn(
        "flex flex-col items-center gap-6 w-full max-w-2xl mx-auto",
        className,
      )}
    >
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">
          You've already played today!
        </h2>
        <p className="text-muted-foreground">
          Come back tomorrow for a new puzzle
        </p>
      </div>

      <div className="bg-base-100 rounded-xl p-6 card-organic w-full">
        <div className="flex items-center justify-center gap-3">
          <Clock className="h-5 w-5 text-primary" />
          <div className="text-center">
            <div className="text-sm text-muted-foreground">Next puzzle in</div>
            <div
              className="text-2xl font-bold text-primary"
              data-testid="countdown"
            >
              {formatCountdown(timeRemaining)}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 w-full">
        <div className="bg-base-100 rounded-xl p-4 card-organic text-center">
          <Trophy className="h-5 w-5 mx-auto mb-2 text-warning" />
          <div className="text-sm text-muted-foreground mb-1">Score</div>
          <div className="text-3xl font-bold" data-testid="final-score">
            {finalScore}
          </div>
        </div>

        {solveTimeMs != null && (
          <div className="bg-base-100 rounded-xl p-4 card-organic text-center">
            <Clock className="h-5 w-5 mx-auto mb-2 text-info" />
            <div className="text-sm text-muted-foreground mb-1">Time</div>
            <div className="text-2xl font-bold" data-testid="solve-time">
              {formatSolveTime(solveTimeMs)}
            </div>
          </div>
        )}

        {leaderboardRank != null && (
          <div className="bg-base-100 rounded-xl p-4 card-organic text-center">
            <TrendingUp className="h-5 w-5 mx-auto mb-2 text-success" />
            <div className="text-sm text-muted-foreground mb-1">Rank</div>
            <div
              className="text-2xl font-bold text-success"
              data-testid="leaderboard-rank"
            >
              #{leaderboardRank}
            </div>
          </div>
        )}
      </div>

      <div className="bg-base-100 rounded-xl p-4 card-organic w-full">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold">Words Found</h3>
          <span className="text-sm text-muted-foreground">
            {wordsFound.length} words
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {wordsFound.map((word) => (
            <span key={word} className="badge badge-lg badge-outline">
              {word}
            </span>
          ))}
        </div>
      </div>

      <button
        type="button"
        className="btn btn-outline btn-lg btn-organic"
        onClick={() => {
          window.location.href = "/leaderboard"
        }}
      >
        <TrendingUp className="mr-2 h-4 w-4" />
        View Leaderboard
      </button>
    </div>
  )
}
