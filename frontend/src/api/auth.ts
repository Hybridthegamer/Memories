import { api } from "./client";

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function registerUser(email: string, password: string): Promise<void> {
  await api.post("/auth/register", { email, password });
}

export async function loginUser(email: string, password: string): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/auth/login", { email, password });
  return data;
}
