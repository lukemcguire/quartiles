import { Sidebar } from "@/components/Common/Sidebar"
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router"

const isLoggedIn = () => {
  return localStorage.getItem("access_token") !== null
}

export const Route = createFileRoute("/_layout")({
  beforeLoad: () => {
    if (!isLoggedIn()) {
      throw redirect({
        to: "/login",
      })
    }
  },
  component: Layout,
})

function Layout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8">
        <Outlet />
      </main>
    </div>
  )
}
