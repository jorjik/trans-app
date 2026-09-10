import { create } from 'zustand';

import type { User } from '../types';

interface AppState {
  token: string | null;
  user: User | null;
  isReady: boolean;
  activeTab: 'dashboard' | 'chats' | 'billing' | 'settings';
  quickText: string;
  quickResult: string | null;
  setToken: (token: string | null) => void;
  setUser: (user: User | null) => void;
  setReady: (ready: boolean) => void;
  setActiveTab: (tab: AppState['activeTab']) => void;
  setQuickText: (text: string) => void;
  setQuickResult: (result: string | null) => void;
}

export const useStore = create<AppState>((set) => ({
  token: null,
  user: null,
  isReady: false,
  activeTab: 'dashboard',
  quickText: '',
  quickResult: null,
  setToken: (token) => set({ token }),
  setUser: (user) => set({ user }),
  setReady: (isReady) => set({ isReady }),
  setActiveTab: (activeTab) => set({ activeTab }),
  setQuickText: (quickText) => set({ quickText }),
  setQuickResult: (quickResult) => set({ quickResult }),
}));
