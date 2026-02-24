"use client"

import { useState, useEffect } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import type { UserAccount, UpdateUserRequest } from "@/types/user"

interface EditUserDialogProps {
  user: UserAccount | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (id: string, data: UpdateUserRequest) => void
  isLoading: boolean
}

export function EditUserDialog({
  user,
  open,
  onOpenChange,
  onSubmit,
  isLoading,
}: EditUserDialogProps) {
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    phone_number: "",
    is_superuser: false,
  })

  useEffect(() => {
    if (user) {
      setForm({
        first_name: user.first_name,
        last_name: user.last_name,
        phone_number: user.phone_number || "",
        is_superuser: user.is_superuser,
      })
    }
  }, [user])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!user) return
    onSubmit(user.id, {
      first_name: form.first_name,
      last_name: form.last_name,
      phone_number: form.phone_number || undefined,
      is_superuser: form.is_superuser,
    })
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Edit User</DialogTitle>
          <DialogDescription>
            Update user account details.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="edit_first_name">First Name</Label>
              <Input
                id="edit_first_name"
                required
                value={form.first_name}
                onChange={(e) =>
                  setForm({ ...form, first_name: e.target.value })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="edit_last_name">Last Name</Label>
              <Input
                id="edit_last_name"
                required
                value={form.last_name}
                onChange={(e) =>
                  setForm({ ...form, last_name: e.target.value })
                }
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit_email">Email</Label>
            <Input id="edit_email" disabled value={user?.email || ""} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="edit_phone_number">Phone Number</Label>
            <Input
              id="edit_phone_number"
              value={form.phone_number}
              onChange={(e) =>
                setForm({ ...form, phone_number: e.target.value })
              }
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="edit_is_superuser"
              checked={form.is_superuser}
              onChange={(e) =>
                setForm({ ...form, is_superuser: e.target.checked })
              }
              className="h-4 w-4 rounded border-gray-300"
            />
            <Label htmlFor="edit_is_superuser">Administrator</Label>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? "Saving..." : "Save Changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
