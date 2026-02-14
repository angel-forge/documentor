import { Outlet } from "react-router-dom"
import { Header } from "./header"

export function MainLayout() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="mx-auto max-w-5xl px-4 py-6 flex-1 overflow-hidden w-full">
        <Outlet />
      </main>
    </div>
  )
}
