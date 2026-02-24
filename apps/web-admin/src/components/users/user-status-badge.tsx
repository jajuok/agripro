import { Badge } from "@/components/ui/badge"

export function UserStatusBadge({ isActive }: { isActive: boolean }) {
  return isActive ? (
    <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
      Active
    </Badge>
  ) : (
    <Badge className="bg-red-100 text-red-800 hover:bg-red-100">
      Inactive
    </Badge>
  )
}
