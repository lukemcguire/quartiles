import { useCallback, useState } from "react"

const PLAYER_STORAGE_KEY = "quartiles_player"
const _PLAYER_VALIDITY_MS = 30 * 24 * 60 * 60 * 1000 // 30 days

interface StoredPlayer {
  playerId: string
  displayName: string
  timestamp: number
}

export function usePlayer() {
  const [playerId, setPlayerId] = useState<string | null>(() =>
    localStorage.getItem(PLAYER_STORAGE_KEY)
      ? JSON.parse(localStorage.getItem(PLAYER_STORAGE_KEY)!).playerId
      : null,
  )
  const [displayName, setDisplayName] = useState<string | null>(() =>
    localStorage.getItem(PLAYER_STORAGE_KEY)
      ? JSON.parse(localStorage.getItem(PLAYER_STORAGE_KEY)!).displayName
      : null,
  )

  const savePlayer = useCallback((id: string, name: string) => {
    const stored: StoredPlayer = {
      playerId: id,
      displayName: name,
      timestamp: Date.now(),
    }
    localStorage.setItem(PLAYER_STORAGE_KEY, JSON.stringify(stored))
    setPlayerId(id)
    setDisplayName(name)
  }, [])

  const clearPlayer = useCallback(() => {
    localStorage.removeItem(PLAYER_STORAGE_KEY)
    setPlayerId(null)
    setDisplayName(null)
  }, [])

  return {
    playerId,
    displayName,
    savePlayer,
    clearPlayer,
    isReturningPlayer: playerId !== null,
  }
}
