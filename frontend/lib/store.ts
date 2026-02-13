import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User } from '@/lib/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  accessToken: string | null;
  refreshToken: string | null;
  login: (user: User) => void;
  loginWithTokens: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      isAuthenticated: false,
      accessToken: null,
      refreshToken: null,
      login: (user) => set({ user, isAuthenticated: true }),
      loginWithTokens: (user, accessToken, refreshToken) =>
        set({ user, isAuthenticated: true, accessToken, refreshToken }),
      logout: () => set({ user: null, isAuthenticated: false, accessToken: null, refreshToken: null }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
