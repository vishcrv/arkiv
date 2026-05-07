import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { authApi } from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser]   = useState(null);
  const [ready, setReady] = useState(false);

  // Restore session from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem("arkiv_token");
    if (!token) { setReady(true); return; }
    authApi.me()
      .then((u) => setUser(u))
      .catch(() => localStorage.removeItem("arkiv_token"))
      .finally(() => setReady(true));
  }, []);

  const _store = useCallback((token, userData) => {
    localStorage.setItem("arkiv_token", token);
    setUser(userData);
  }, []);

  const login = useCallback(async (email, password) => {
    const { token, user: u } = await authApi.login({ email, password });
    _store(token, u);
    return u;
  }, [_store]);

  const register = useCallback(async (email, username, password) => {
    const { token, user: u } = await authApi.register({ email, username, password });
    _store(token, u);
    return u;
  }, [_store]);

  const googleLogin = useCallback(async (idToken) => {
    const { token, user: u } = await authApi.google({ id_token: idToken });
    _store(token, u);
    return u;
  }, [_store]);

  const logout = useCallback(() => {
    localStorage.removeItem("arkiv_token");
    setUser(null);
  }, []);

  const updateUser = useCallback((partial) => {
    setUser((prev) => ({ ...prev, ...partial }));
  }, []);

  return (
    <AuthContext.Provider value={{ user, ready, login, register, googleLogin, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
