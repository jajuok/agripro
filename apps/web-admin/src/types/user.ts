export interface UserAccount {
  id: string
  email: string
  first_name: string
  last_name: string
  phone_number: string | null
  is_active: boolean
  is_superuser: boolean
  totp_enabled: boolean
  created_at: string
  last_login: string | null
}

export interface CreateUserRequest {
  email: string
  password: string
  first_name: string
  last_name: string
  phone_number?: string
  is_superuser?: boolean
}

export interface UpdateUserRequest {
  first_name?: string
  last_name?: string
  phone_number?: string
  is_active?: boolean
  is_superuser?: boolean
}

export interface UserListResponse {
  items: UserAccount[]
  total: number
  page: number
  size: number
  pages: number
}
