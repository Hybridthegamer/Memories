import { createContext, useContext, useState, ReactNode } from "react";
import { loginUser, registerUser } from "../api/auth";

interface AuthContextValue {
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("access_token"));

  async function login(email: string, password: string) {
    const data = await loginUser(email, password);
    localStorage.setItem("access_token", data.access_token);
    setIsAuthenticated(true);
  }

  async function register(email: string, password: string) {
    await registerUser(email, password);
    await login(email, password);
  }

  function logout() {
    localStorage.removeItem("access_token");
    setIsAuthenticated(false);
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
