import { authClient } from "./api-client"
import type {
  UserAccount,
  UserListResponse,
  CreateUserRequest,
  UpdateUserRequest,
} from "@/types/user"

export interface UserListParams {
  page?: number
  size?: number
  search?: string
  is_active?: boolean
}

export const userApi = {
  list: async (params: UserListParams = {}): Promise<UserListResponse> => {
    const response = await authClient.get<UserListResponse>("/admin/users", {
      params,
    })
    return response.data
  },

  getById: async (id: string): Promise<UserAccount> => {
    // Fetch from list with search — no dedicated single-user admin endpoint yet
    // We'll use the list endpoint and filter
    const response = await authClient.get<UserListResponse>("/admin/users", {
      params: { size: 100 },
    })
    const user = response.data.items.find((u) => u.id === id)
    if (!user) throw new Error("User not found")
    return user
  },

  create: async (data: CreateUserRequest): Promise<UserAccount> => {
    const response = await authClient.post<UserAccount>("/admin/users", data)
    return response.data
  },

  update: async (
    id: string,
    data: UpdateUserRequest
  ): Promise<UserAccount> => {
    const response = await authClient.patch<UserAccount>(
      `/admin/users/${id}`,
      data
    )
    return response.data
  },

  toggleActive: async (id: string): Promise<UserAccount> => {
    const response = await authClient.post<UserAccount>(
      `/admin/users/${id}/toggle-active`
    )
    return response.data
  },

  delete: async (id: string): Promise<void> => {
    await authClient.delete(`/admin/users/${id}`)
  },

  getRoles: async (id: string): Promise<{ id: string; name: string }[]> => {
    const response = await authClient.get<
      { id: string; name: string; description: string | null }[]
    >(`/admin/users/${id}/roles`)
    return response.data
  },
}
