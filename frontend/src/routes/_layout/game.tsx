import { createFileRoute } from "@tanstack/react-router"
import { Game } from "@/components/Game"

export const Route = createFileRoute("/_layout/game")({
  component: GamePage,
})

function GamePage() {
  return (
    <div className="flex flex-col items-center gap-8 py-4 animate-fade-in">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">Daily Quartiles</h1>
        <p className="text-muted-foreground mt-2">
          Find words using adjacent tiles. Discover all 4 quartiles to complete
          the puzzle!
        </p>
      </div>

      <Game />
    </div>
  )
}
