import { UserSettings } from "@/components/Common/UserSettings"
import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/settings")({
  component: Settings,
})

function Settings() {
  return (
    <div className="container mx-auto max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>
      <UserSettings />
    </div>
  )
}
