"use client"

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import type { UserAccount } from "@/types/user"

interface DeleteUserDialogProps {
  user: UserAccount | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (id: string) => void
  isLoading: boolean
}

export function DeleteUserDialog({
  user,
  open,
  onOpenChange,
  onConfirm,
  isLoading,
}: DeleteUserDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete User</DialogTitle>
          <DialogDescription>
            Are you sure you want to permanently delete{" "}
            <strong>
              {user?.first_name} {user?.last_name}
            </strong>{" "}
            ({user?.email})? This action cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={() => user && onConfirm(user.id)}
            disabled={isLoading}
          >
            {isLoading ? "Deleting..." : "Delete User"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
