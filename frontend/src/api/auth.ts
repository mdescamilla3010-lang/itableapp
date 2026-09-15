import { api } from "./client";
import type { LoginResult } from "./types";

export const authApi = {
  login: (email: string, password: string) =>
    api.post<LoginResult>("/auth/login", { email, password }),
};
