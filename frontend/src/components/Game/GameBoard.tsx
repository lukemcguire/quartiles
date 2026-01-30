import { Tile } from "./Tile"

export interface GameBoardProps {
  tiles: Array<{ id: number; letters: string }>
  selectedTileIds: number[]
  usedTileIds: Set<number>
  onTileClick: (tileId: number) => void
  disabled?: boolean
}

export function GameBoard({
  tiles,
  selectedTileIds,
  usedTileIds,
  onTileClick,
  disabled,
}: GameBoardProps) {
  return (
    <div
      className="grid grid-cols-4 gap-3 sm:gap-4 p-4 sm:p-6 bg-base-200/50 rounded-2xl card-organic"
      data-testid="game-board"
    >
      {tiles.map((tile, index) => {
        const isSelected = selectedTileIds.includes(tile.id)
        const isUsed = usedTileIds.has(tile.id)

        return (
          <div
            key={tile.id}
            className="aspect-square"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <Tile
              id={tile.id}
              letters={tile.letters}
              isSelected={isSelected}
              isUsed={isUsed}
              onClick={() => onTileClick(tile.id)}
              disabled={disabled}
            />
          </div>
        )
      })}
    </div>
  )
}
