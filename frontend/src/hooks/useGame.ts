import { useMutation, useQuery } from "@tanstack/react-query"

import { GameService } from "@/client"

export interface GameSession {
  sessionId: string
  playerId: string
  displayName: string
  tiles: Array<{ id: number; letters: string }>
  alreadyPlayed: boolean
  previousResult?: {
    finalScore: number
    solveTimeMs?: number | null
    wordsFound: Array<string>
    leaderboardRank?: number | null
  }
}

export interface WordValidation {
  isValid: boolean
  points?: number | null
  reason?: string | null
  isQuartile?: boolean
  currentScore: number
  isSolved: boolean
}

export interface Hint {
  hintNumber: number
  definition?: string | null
  timePenaltyMs: number
  quartilesRemaining: number
}

const getDeviceFingerprint = (): string => {
  let fingerprint = localStorage.getItem("device_fingerprint")
  if (!fingerprint) {
    fingerprint = crypto.randomUUID()
    localStorage.setItem("device_fingerprint", fingerprint)
  }
  return fingerprint
}

export const useGameStart = () => {
  return useMutation<GameSession, Error, void>({
    mutationFn: async () => {
      const response = await GameService.startGame({
        requestBody: {
          device_fingerprint: getDeviceFingerprint(),
        },
      })
      return {
        sessionId: response.session_id,
        playerId: response.player_id,
        displayName: response.display_name,
        tiles: response.tiles,
        alreadyPlayed: response.already_played,
        previousResult: response.previous_result
          ? {
              finalScore: response.previous_result.final_score,
              solveTimeMs: response.previous_result.solve_time_ms,
              wordsFound: response.previous_result.words_found,
              leaderboardRank: response.previous_result.leaderboard_rank,
            }
          : undefined,
      }
    },
  })
}

export const useValidateWord = () => {
  return useMutation<
    WordValidation,
    Error,
    { sessionId: string; word: string }
  >({
    mutationFn: async ({ sessionId, word }) => {
      const response = await GameService.validateWord({
        sessionId,
        requestBody: { word },
      })
      return {
        isValid: response.is_valid,
        points: response.points,
        reason: response.reason,
        isQuartile: response.is_quartile,
        currentScore: response.current_score,
        isSolved: response.is_solved,
      }
    },
  })
}

export const useSubmitGame = () => {
  return useMutation<
    {
      success: boolean
      finalScore: number
      solveTimeMs?: number | null
      leaderboardRank?: number | null
      message: string
    },
    Error,
    string
  >({
    mutationFn: async (sessionId) => {
      const response = await GameService.submitGame({ sessionId })
      return {
        success: response.success,
        finalScore: response.final_score,
        solveTimeMs: response.solve_time_ms,
        leaderboardRank: response.leaderboard_rank,
        message: response.message,
      }
    },
  })
}

export const useGetHint = () => {
  return useMutation<Hint, Error, string>({
    mutationFn: async (sessionId) => {
      const response = await GameService.getHint({ sessionId })
      return {
        hintNumber: response.hint_number,
        definition: response.definition,
        timePenaltyMs: response.time_penalty_ms,
        quartilesRemaining: response.quartiles_remaining,
      }
    },
  })
}

export const useLeaderboard = (playerId?: string | null, limit = 10) => {
  return useQuery({
    queryKey: ["leaderboard", "today", playerId, limit],
    queryFn: async () => {
      return await LeaderboardService.getTodaysLeaderboard({
        limit,
        playerId,
      })
    },
    staleTime: 30000, // 30 seconds
  })
}

import { LeaderboardService } from "@/client"
