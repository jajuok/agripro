"use client"

import { useState, useMemo } from "react"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { userApi } from "@/services/user-api"
import { UserFilters } from "@/components/users/user-filters"
import { UserTable } from "@/components/users/user-table"
import { CreateUserDialog } from "@/components/users/create-user-dialog"
import { EditUserDialog } from "@/components/users/edit-user-dialog"
import { DeleteUserDialog } from "@/components/users/delete-user-dialog"
import { Button } from "@/components/ui/button"
import { UserPlus } from "lucide-react"
import type { UserAccount, CreateUserRequest, UpdateUserRequest } from "@/types/user"

const PAGE_SIZE = 20

export default function UsersPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")

  // Dialogs
  const [createOpen, setCreateOpen] = useState(false)
  const [editUser, setEditUser] = useState<UserAccount | null>(null)
  const [deleteUser, setDeleteUser] = useState<UserAccount | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ["users", page, search, statusFilter],
    queryFn: () =>
      userApi.list({
        page,
        size: PAGE_SIZE,
        search: search || undefined,
        is_active:
          statusFilter === "active"
            ? true
            : statusFilter === "inactive"
            ? false
            : undefined,
      }),
  })

  const filteredUsers = useMemo(() => {
    return data?.items || []
  }, [data?.items])

  const totalPages = data?.pages || 1

  const createMutation = useMutation({
    mutationFn: (req: CreateUserRequest) => userApi.create(req),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      setCreateOpen(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateUserRequest }) =>
      userApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      setEditUser(null)
    },
  })

  const toggleMutation = useMutation({
    mutationFn: (id: string) => userApi.toggleActive(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => userApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
      setDeleteUser(null)
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Users</h1>
          <p className="text-muted-foreground">
            Manage user accounts ({data?.total || 0} total)
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)}>
          <UserPlus className="h-4 w-4 mr-2" />
          Add User
        </Button>
      </div>

      <UserFilters
        search={search}
        onSearchChange={(v) => {
          setSearch(v)
          setPage(1)
        }}
        statusFilter={statusFilter}
        onStatusFilterChange={(v) => {
          setStatusFilter(v)
          setPage(1)
        }}
      />

      <UserTable
        users={filteredUsers}
        isLoading={isLoading}
        page={page}
        totalPages={totalPages}
        onPageChange={setPage}
        onEdit={setEditUser}
        onToggleActive={(user) => toggleMutation.mutate(user.id)}
        onDelete={setDeleteUser}
      />

      <CreateUserDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onSubmit={(data) => createMutation.mutate(data)}
        isLoading={createMutation.isPending}
      />

      <EditUserDialog
        user={editUser}
        open={!!editUser}
        onOpenChange={(open) => !open && setEditUser(null)}
        onSubmit={(id, data) => updateMutation.mutate({ id, data })}
        isLoading={updateMutation.isPending}
      />

      <DeleteUserDialog
        user={deleteUser}
        open={!!deleteUser}
        onOpenChange={(open) => !open && setDeleteUser(null)}
        onConfirm={(id) => deleteMutation.mutate(id)}
        isLoading={deleteMutation.isPending}
      />
    </div>
  )
}
