import { NavLink } from "react-router-dom"
import { BookOpen, FileText, Upload, MessageSquare } from "lucide-react"
import { useHealth } from "@/hooks/use-health"
import { cn } from "@/lib/utils"

const navItems = [
  { to: "/ask", label: "Ask", icon: MessageSquare },
  { to: "/documents", label: "Documents", icon: FileText },
  { to: "/ingest", label: "Ingest", icon: Upload },
]

export function Header() {
  const { data, isError } = useHealth()
  const isHealthy = !!data && !isError

  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex h-14 max-w-5xl items-center gap-6 px-4">
        <NavLink to="/" className="flex items-center gap-2 font-semibold">
          <BookOpen className="h-5 w-5" />
          <span>DocuMentor</span>
        </NavLink>

        <nav className="flex items-center gap-1">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2 text-sm text-muted-foreground">
          <span
            className={cn(
              "h-2 w-2 rounded-full",
              isHealthy ? "bg-green-500" : "bg-red-500",
            )}
          />
          <span className="hidden sm:inline">
            {isHealthy ? "API connected" : "API unavailable"}
          </span>
        </div>
      </div>
    </header>
  )
}
