import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { fetchMe, login as apiLogin, logoutStorage, readStoredSession, storeSession } from "../api/auth";
import type { AuthSession, User } from "./types";

type AuthContextValue = {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<User>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  setSession: (session: AuthSession) => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const setSession = useCallback((session: AuthSession) => {
    storeSession(session);
    setToken(session.accessToken);
    setUser(session.user);
  }, []);

  const logout = useCallback(() => {
    logoutStorage();
    setToken(null);
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    if (!token) return;
    const me = await fetchMe(token);
    setUser(me.user);
    const stored = readStoredSession();
    if (stored) {
      storeSession({ accessToken: stored.accessToken, user: me.user });
    }
  }, [token]);

  useEffect(() => {
    const stored = readStoredSession();
    if (!stored) {
      setLoading(false);
      return;
    }
    setToken(stored.accessToken);
    setUser(stored.user);
    fetchMe(stored.accessToken)
      .then((me) => {
        setUser(me.user);
        storeSession({ accessToken: stored.accessToken, user: me.user });
      })
      .catch(() => logout())
      .finally(() => setLoading(false));
  }, [logout]);

  const login = useCallback(
    async (username: string, password: string) => {
      const session = await apiLogin(username, password);
      setSession(session);
      return session.user;
    },
    [setSession],
  );

  const value = useMemo(
    () => ({ user, token, loading, login, logout, refreshUser, setSession }),
    [user, token, loading, login, logout, refreshUser, setSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth fora de AuthProvider");
  return ctx;
}
