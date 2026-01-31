import { useCallback, useEffect, useState } from "react"

export interface KeyboardNavigationOptions {
  tileCount: number
  columns: number
  onTileSelect: (index: number) => void
  onClear: () => void
  onSubmit: () => void
  disabled?: boolean
}

export interface KeyboardNavigationReturn {
  focusedIndex: number | null
  keyHandlers: {
    onKeyDown: (e: React.KeyboardEvent<HTMLDivElement>) => void
  }
}

const GRID_COLUMNS = 4
const GRID_SIZE = 20

/**
 * Check if index is on the left edge of the grid
 * Left edge indices: 0, 4, 8, 12, 16
 */
function isLeftEdge(index: number): boolean {
  return index % GRID_COLUMNS === 0
}

/**
 * Check if index is on the right edge of the grid
 * Right edge indices: 3, 7, 11, 15, 19
 */
function isRightEdge(index: number): boolean {
  return (index + 1) % GRID_COLUMNS === 0
}

/**
 * Check if index is on the top row
 * Top row indices: 0, 1, 2, 3
 */
function isTopRow(index: number): boolean {
  return index < GRID_COLUMNS
}

/**
 * Check if index is on the bottom row
 * Bottom row indices: 16, 17, 18, 19
 */
function isBottomRow(index: number): boolean {
  return index >= GRID_SIZE - GRID_COLUMNS
}

/**
 * Hook for keyboard navigation in the game grid.
 *
 * Key bindings:
 * - ArrowUp/k: Move focus up
 * - ArrowDown/j: Move focus down
 * - ArrowLeft/h: Move focus left
 * - ArrowRight/l: Move focus right
 * - Enter/Space: Select focused tile
 * - Shift+Enter: Submit word
 * - Escape: Clear selection
 *
 * Navigation stops at grid edges.
 */
export function useKeyboardNavigation({
  tileCount,
  columns,
  onTileSelect,
  onClear,
  onSubmit,
  disabled = false,
}: KeyboardNavigationOptions): KeyboardNavigationReturn {
  const [focusedIndex, setFocusedIndex] = useState<number | null>(null)

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (disabled) return

      // Only handle keys that we care about
      const isNavigationKey =
        e.key === "ArrowUp" ||
        e.key === "ArrowDown" ||
        e.key === "ArrowLeft" ||
        e.key === "ArrowRight" ||
        e.key === "k" ||
        e.key === "j" ||
        e.key === "h" ||
        e.key === "l" ||
        e.key === "Enter" ||
        e.key === " " ||
        e.key === "Escape"

      if (!isNavigationKey) return

      // Don't prevent default for other keys
      e.preventDefault()

      let newIndex: number | null = focusedIndex

      switch (e.key) {
        case "ArrowUp":
        case "k":
          if (focusedIndex !== null && !isTopRow(focusedIndex)) {
            newIndex = focusedIndex - columns
          }
          break
        case "ArrowDown":
        case "j":
          if (focusedIndex !== null && !isBottomRow(focusedIndex)) {
            newIndex = focusedIndex + columns
          }
          break
        case "ArrowLeft":
        case "h":
          if (focusedIndex !== null && !isLeftEdge(focusedIndex)) {
            newIndex = focusedIndex - 1
          }
          break
        case "ArrowRight":
        case "l":
          if (focusedIndex !== null && !isRightEdge(focusedIndex)) {
            newIndex = focusedIndex + 1
          }
          break
        case "Enter":
          if (e.shiftKey) {
            // Shift+Enter: Submit word
            onSubmit()
          } else if (focusedIndex !== null) {
            // Regular Enter: Select focused tile
            onTileSelect(focusedIndex)
          }
          return
        case " ":
          // Space: Select focused tile
          if (focusedIndex !== null) {
            onTileSelect(focusedIndex)
          }
          return
        case "Escape":
          // Clear selection
          onClear()
          return
        default:
          return
      }

      // Update focus if changed
      if (
        newIndex !== null &&
        newIndex !== focusedIndex &&
        newIndex >= 0 &&
        newIndex < tileCount
      ) {
        setFocusedIndex(newIndex)
      }
    },
    [
      disabled,
      focusedIndex,
      tileCount,
      columns,
      onTileSelect,
      onClear,
      onSubmit,
    ],
  )

  // Reset focus when disabled changes to true
  useEffect(() => {
    if (disabled) {
      setFocusedIndex(null)
    }
  }, [disabled])

  return {
    focusedIndex,
    keyHandlers: {
      onKeyDown: handleKeyDown,
    },
  }
}
