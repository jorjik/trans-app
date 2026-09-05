import { MantineProvider } from '@mantine/core';
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { ReactNode } from 'react';

import App from '../App';
import type { User } from '../types';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <MantineProvider>
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      </MantineProvider>
    );
  };
}

// Mock API client
vi.mock('../api/client', () => ({
  authWithTelegram: vi.fn().mockResolvedValue({
    access_token: 'test-token',
    token_type: 'bearer',
    expires_in: 3600,
    user: {
      id: 123,
      ui_language: 'en',
      target_language: 'en',
      favorite_langs: [],
      preferred_engine: 'auto',
      plan: 'free',
      chars_limit: 25000,
      chars_used: 0,
      chars_remaining: 25000,
      reset_at: null,
      created_at: '2025-01-01T00:00:00Z',
    },
    is_new: true,
  }),
  getMe: vi.fn().mockResolvedValue({
    id: 123,
    ui_language: 'en',
    target_language: 'en',
    favorite_langs: [],
    preferred_engine: 'auto',
    plan: 'free',
    chars_limit: 25000,
    chars_used: 0,
    chars_remaining: 25000,
    reset_at: null,
    created_at: '2025-01-01T00:00:00Z',
  }),
  updateMe: vi.fn(),
  getChats: vi.fn().mockResolvedValue({ items: [], total: 0, limit_reached: false, max_chats: 5 }),
  getPlans: vi.fn().mockResolvedValue({ plans: [], current_plan: 'free' }),
  getStats: vi.fn().mockResolvedValue({
    period: '30d',
    total_chars: 0,
    total_requests: 0,
    chars_by_day: [],
    top_languages: [],
    providers_used: {},
  }),
  createChat: vi.fn(),
  updateChat: vi.fn(),
  deleteChat: vi.fn(),
  createCheckout: vi.fn(),
}));

// Mock i18n — returns the key as-is for simplicity
vi.mock('../i18n', () => ({
  t: (key: string, lang: string) => `${key} (${lang})`,
  LANG_NAMES_LOCALIZED: {},
}));

// Mock useStore — real store with Zustand
import { useStore } from '../store/useStore';

describe('Language Picker — handleLangConfirm', () => {
  beforeEach(() => {
    // Reset store before each test
    useStore.setState({
      token: null,
      user: null,
      isReady: false,
      activeTab: 'dashboard',
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it('renders language picker for new user', async () => {
    const wrapper = createWrapper();
    render(<App />, { wrapper });

    // Wait for auth to complete and picker to render
    await waitFor(() => {
      expect(screen.getByText(/langpicker\.title/)).toBeInTheDocument();
    });

    // Should show 3 language options
    expect(screen.getByText(/langpicker\.en/)).toBeInTheDocument();
    expect(screen.getByText(/langpicker\.ru/)).toBeInTheDocument();
    expect(screen.getByText(/langpicker\.uk/)).toBeInTheDocument();

    // Should show Continue button
    expect(screen.getByText(/langpicker\.continue/)).toBeInTheDocument();
  });

  it('sends only ui_language (not target_language) on confirm', async () => {
    const { updateMe } = await import('../api/client');
    const mockUpdateMe = vi.mocked(updateMe).mockResolvedValue({
      id: 123,
      ui_language: 'ru',
      target_language: 'en',
      favorite_langs: [],
      preferred_engine: 'auto',
      plan: 'free',
      chars_limit: 25000,
      chars_used: 0,
      chars_remaining: 25000,
      reset_at: null,
      created_at: '2025-01-01T00:00:00Z',
    });

    const wrapper = createWrapper();
    render(<App />, { wrapper });

    // Wait for picker
    await waitFor(() => {
      expect(screen.getByText(/langpicker\.title/)).toBeInTheDocument();
    });

    // Click Russian
    fireEvent.click(screen.getByText(/langpicker\.ru/));

    // Click Continue
    fireEvent.click(screen.getByText(/langpicker\.continue/));

    await waitFor(() => {
      expect(mockUpdateMe).toHaveBeenCalledWith('test-token', {
        ui_language: 'ru',
      });
    });

    // Should NOT include target_language
    expect(mockUpdateMe).not.toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ target_language: expect.anything() }),
    );
  });

  it('sets user immediately after confirm and invalidates query', async () => {
    const { updateMe, getMe } = await import('../api/client');

    const updatedUser: User = {
      id: 123,
      ui_language: 'ru',
      target_language: 'en',
      favorite_langs: [],
      preferred_engine: 'auto',
      plan: 'free',
      chars_limit: 25000,
      chars_used: 0,
      chars_remaining: 25000,
      reset_at: null,
      created_at: '2025-01-01T00:00:00Z',
    };

    vi.mocked(updateMe).mockResolvedValue(updatedUser);
    vi.mocked(getMe).mockResolvedValue(updatedUser);

    const wrapper = createWrapper();
    render(<App />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/langpicker\.title/)).toBeInTheDocument();
    });

    // Click Russian
    fireEvent.click(screen.getByText(/langpicker\.ru/));
    // Click Continue
    fireEvent.click(screen.getByText(/langpicker\.continue/));

    // After confirm, isNewUser becomes false, so main app should render
    await waitFor(() => {
      // Main app shows dashboard or nav — check for nav.dashboard
      expect(screen.getByText(/nav\.dashboard/)).toBeInTheDocument();
    });

    // User in store should have ui_language = 'ru'
    const state = useStore.getState();
    expect(state.user?.ui_language).toBe('ru');
  });

  it('shows main app in selected language after picker confirm', async () => {
    const { updateMe } = await import('../api/client');

    vi.mocked(updateMe).mockResolvedValue({
      id: 123,
      ui_language: 'ru',
      target_language: 'en',
      favorite_langs: [],
      preferred_engine: 'auto',
      plan: 'free',
      chars_limit: 25000,
      chars_used: 0,
      chars_remaining: 25000,
      reset_at: null,
      created_at: '2025-01-01T00:00:00Z',
    });

    const wrapper = createWrapper();
    render(<App />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/langpicker\.title/)).toBeInTheDocument();
    });

    // Pick Russian
    fireEvent.click(screen.getByText(/langpicker\.ru/));
    // Confirm
    fireEvent.click(screen.getByText(/langpicker\.continue/));

    // Main app should appear with Russian language
    await waitFor(() => {
      expect(screen.getByText(/nav\.dashboard/)).toBeInTheDocument();
    });

    // Verify user has ui_language = 'ru'
    const state = useStore.getState();
    expect(state.user?.ui_language).toBe('ru');
  });

  it('does not overwrite ui_language with stale meQuery data', async () => {
    const { updateMe, getMe } = await import('../api/client');

    // First getMe call returns old data (English)
    vi.mocked(getMe).mockResolvedValue({
      id: 123,
      ui_language: 'en',
      target_language: 'en',
      favorite_langs: [],
      preferred_engine: 'auto',
      plan: 'free',
      chars_limit: 25000,
      chars_used: 0,
      chars_remaining: 25000,
      reset_at: null,
      created_at: '2025-01-01T00:00:00Z',
    });

    // updateMe returns updated data (Russian)
    vi.mocked(updateMe).mockResolvedValue({
      id: 123,
      ui_language: 'ru',
      target_language: 'en',
      favorite_langs: [],
      preferred_engine: 'auto',
      plan: 'free',
      chars_limit: 25000,
      chars_used: 0,
      chars_remaining: 25000,
      reset_at: null,
      created_at: '2025-01-01T00:00:00Z',
    });

    const wrapper = createWrapper();
    render(<App />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/langpicker\.title/)).toBeInTheDocument();
    });

    // Pick Russian
    fireEvent.click(screen.getByText(/langpicker\.ru/));
    // Confirm
    fireEvent.click(screen.getByText(/langpicker\.continue/));

    // After confirm + invalidate, getMe should be called again (refetch)
    await waitFor(() => {
      // When meQuery refetches, it should get the updated user (ru)
      expect(vi.mocked(getMe)).toHaveBeenCalledTimes(2);
    });

    // ui_language should still be 'ru'
    const state = useStore.getState();
    expect(state.user?.ui_language).toBe('ru');
  });
});
