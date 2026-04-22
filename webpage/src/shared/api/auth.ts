export interface UserPublic {
  id: number;
  email: string | null;
  phone: string | null;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterResponse extends AuthTokens {
  user: UserPublic;
}

export interface RegisterPayload {
  email?: string;
  phone?: string;
  password: string;
}

export interface LoginPayload {
  account: string;
  password: string;
}
