"use client"

import { useState } from "react"
import { useParams, useRouter } from "next/navigation"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { userApi } from "@/services/user-api"
import { EditUserDialog } from "@/components/users/edit-user-dialog"
import { DeleteUserDialog } from "@/components/users/delete-user-dialog"
import { UserStatusBadge } from "@/components/users/user-status-badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ArrowLeft, Pencil, Power, Trash2 } from "lucide-react"
import { formatDateTime } from "@/lib/utils"
import type { UpdateUserRequest } from "@/types/user"

export default function UserDetailPage() {
  const params = useParams()
  const id = (params?.id as string) || ""
  const router = useRouter()
  const queryClient = useQueryClient()

  const [editOpen, setEditOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)

  const { data: user, isLoading } = useQuery({
    queryKey: ["users", id],
    queryFn: () => userApi.getById(id),
    enabled: !!id,
  })

  const { data: roles } = useQuery({
    queryKey: ["users", id, "roles"],
    queryFn: () => userApi.getRoles(id),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserRequest }) =>
      userApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      setEditOpen(false)
    },
  })

  const toggleMutation = useMutation({
    mutationFn: (userId: string) => userApi.toggleActive(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (userId: string) => userApi.delete(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      router.push("/users")
    },
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!user) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">User not found</p>
        <Button variant="outline" className="mt-4" onClick={() => router.push("/users")}>
          Back to Users
        </Button>
      </div>
    )
  }

  const infoItems = [
    { label: "Email", value: user.email },
    { label: "Phone", value: user.phone_number || "\u2014" },
    { label: "Created", value: formatDateTime(user.created_at) },
    { label: "Last Login", value: user.last_login ? formatDateTime(user.last_login) : "Never" },
    { label: "2FA", value: user.totp_enabled ? "Enabled" : "Disabled" },
    { label: "Role", value: user.is_superuser ? "Administrator" : "User" },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push("/users")}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary text-lg font-semibold">
              {user.first_name[0]}
              {user.last_name[0]}
            </div>
            <div>
              <h1 className="text-2xl font-bold">
                {user.first_name} {user.last_name}
              </h1>
              <p className="text-muted-foreground">{user.email}</p>
            </div>
            <UserStatusBadge isActive={user.is_active} />
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setEditOpen(true)}>
            <Pencil className="h-4 w-4 mr-1" />
            Edit
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => toggleMutation.mutate(user.id)}
          >
            <Power className="h-4 w-4 mr-1" />
            {user.is_active ? "Disable" : "Enable"}
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setDeleteOpen(true)}
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Delete
          </Button>
        </div>
      </div>

      {/* Info Grid */}
      <Card>
        <CardHeader>
          <CardTitle>Account Information</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            {infoItems.map((item) => (
              <div key={item.label}>
                <dt className="text-sm text-muted-foreground">{item.label}</dt>
                <dd className="text-sm font-medium mt-1">{item.value}</dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>

      {/* Roles */}
      <Card>
        <CardHeader>
          <CardTitle>Roles</CardTitle>
        </CardHeader>
        <CardContent>
          {roles && roles.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {roles.map((role) => (
                <Badge key={role.id} variant="secondary">
                  {role.name}
                </Badge>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">No roles assigned</p>
          )}
        </CardContent>
      </Card>

      <EditUserDialog
        user={user}
        open={editOpen}
        onOpenChange={setEditOpen}
        onSubmit={(uid, data) => updateMutation.mutate({ id: uid, data })}
        isLoading={updateMutation.isPending}
      />

      <DeleteUserDialog
        user={user}
        open={deleteOpen}
        onOpenChange={setDeleteOpen}
        onConfirm={(uid) => deleteMutation.mutate(uid)}
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
