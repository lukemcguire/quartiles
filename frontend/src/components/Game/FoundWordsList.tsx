import { cn } from "@/lib/utils"

export interface FoundWord {
  word: string
  points: number
  isQuartile: boolean
}

export interface FoundWordsListProps {
  words: FoundWord[]
  className?: string
}

export function FoundWordsList({ words, className }: FoundWordsListProps) {
  // Sort by points descending, then by word alphabetically
  const sortedWords = [...words].sort((a, b) => {
    if (a.isQuartile && !b.isQuartile) return -1
    if (!a.isQuartile && b.isQuartile) return 1
    if (a.points !== b.points) return b.points - a.points
    return a.word.localeCompare(b.word)
  })

  return (
    <div className={cn("bg-base-100 rounded-xl p-4 card-organic", className)}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">Found Words</h3>
        <span className="text-sm text-muted-foreground">
          {words.length} words
        </span>
      </div>

      {words.length === 0 ? (
        <p className="text-sm text-muted-foreground text-center py-8">
          No words found yet. Start selecting tiles!
        </p>
      ) : (
        <div className="space-y-2 max-h-[300px] overflow-y-auto">
          {sortedWords.map((found, index) => (
            <div
              key={found.word}
              className={cn(
                "flex items-center justify-between p-2 rounded-lg",
                "animate-slide-up",
                found.isQuartile
                  ? "bg-success/10 border border-success/20"
                  : "bg-base-200/50",
              )}
              style={{ animationDelay: `${index * 30}ms` }}
            >
              <div className="flex items-center gap-2">
                {found.isQuartile && (
                  <span
                    className="text-success"
                    role="img"
                    aria-label="Quartile word"
                  >
                    ★
                  </span>
                )}
                <span
                  className={cn(
                    "font-medium",
                    found.isQuartile && "text-success font-semibold",
                  )}
                >
                  {found.word}
                </span>
              </div>
              <span
                className={cn(
                  "text-sm font-semibold",
                  found.isQuartile ? "text-success" : "text-muted-foreground",
                )}
              >
                +{found.points}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
