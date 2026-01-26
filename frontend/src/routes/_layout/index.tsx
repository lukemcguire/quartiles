import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function Dashboard() {
  return (
    <div className="container mx-auto">
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>
      <p className="text-muted-foreground">
        Welcome to Quartiles! This is your dashboard.
      </p>
    </div>
  )
}
