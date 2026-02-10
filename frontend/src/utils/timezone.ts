/**
 * Get the local puzzle date as YYYY-MM-DD string.
 * Uses the client's local timezone to determine "today".
 */
export function getLocalPuzzleDate(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, "0")
  const day = String(now.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}

/**
 * Get milliseconds until next local midnight.
 */
export function getTimeUntilNextPuzzle(): number {
  const now = new Date()
  const tomorrow = new Date(now)
  tomorrow.setDate(tomorrow.getDate() + 1)
  tomorrow.setHours(0, 0, 0, 0)
  return tomorrow.getTime() - now.getTime()
}

/**
 * Format milliseconds into "Xh Ym Zs" format for countdown display.
 */
export function formatCountdown(ms: number): string {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  const remainingSeconds = seconds % 60
  const parts = []
  if (hours > 0) parts.push(`${hours}h`)
  if (remainingMinutes > 0) parts.push(`${remainingMinutes}m`)
  if (remainingSeconds > 0 || parts.length === 0)
    parts.push(`${remainingSeconds}s`)
  return parts.join(" ")
}
