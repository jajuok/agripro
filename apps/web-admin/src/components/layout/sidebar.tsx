"use client"

import { LayoutDashboard, Users, UserCog, Leaf } from "lucide-react"
import { cn } from "@/lib/utils"
import { useUIStore } from "@/store/ui-store"
import { SidebarNavItem } from "./sidebar-nav-item"
import { TooltipProvider } from "@/components/ui/tooltip"
import { Separator } from "@/components/ui/separator"

const navItems = [
  { href: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/farmers", icon: Users, label: "Farmers" },
  { href: "/users", icon: UserCog, label: "Users" },
]

export function Sidebar() {
  const collapsed = useUIStore((s) => s.sidebarCollapsed)

  return (
    <TooltipProvider>
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-30 flex flex-col border-r bg-card transition-all duration-300",
          collapsed ? "w-16" : "w-64"
        )}
      >
        {/* Logo */}
        <div className={cn("flex h-16 items-center border-b px-4", collapsed && "justify-center px-0")}>
          <Leaf className="h-7 w-7 text-primary shrink-0" />
          {!collapsed && <span className="ml-2 text-lg font-bold">AgriPro</span>}
        </div>

        {/* Navigation */}
        <nav className={cn("flex-1 space-y-1 p-3", collapsed && "px-2")}>
          {navItems.map((item) => (
            <SidebarNavItem key={item.href} {...item} collapsed={collapsed} />
          ))}
        </nav>

        <Separator />
        <div className={cn("p-3 text-xs text-muted-foreground", collapsed ? "text-center" : "")}>
          {collapsed ? "v1" : "AgriPro v1.0"}
        </div>
      </aside>
    </TooltipProvider>
  )
}
