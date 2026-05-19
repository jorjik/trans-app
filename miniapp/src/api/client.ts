import type {
  AuthResponse,
  BillingPlansResponse,
  ChatConfig,
  ChatsResponse,
  CheckoutResponse,
  StatsResponse,
  TranslateRequest,
  TranslateResponse,
  User,
} from '../types';

const API_URL = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? 'http://localhost:8000';

async function request<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(init.headers);

  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json');
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let message = `Request failed: ${response.status}`;

    try {
      const data = (await response.json()) as {
        message?: string;
        error?: string;
        detail?: unknown;
      };
      message = data.message ?? data.error ?? message;

      if (message === `Request failed: ${response.status}` && data.detail !== undefined) {
        if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          message = data.detail
            .map((row: { msg?: string; loc?: unknown }) => row.msg ?? JSON.stringify(row))
            .join('; ');
        }
      }
    } catch {
      // ignore non-json errors
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function authWithTelegram(initData: string) {
  return request<AuthResponse>('/auth/telegram', {
    method: 'POST',
    body: JSON.stringify({ init_data: initData }),
  });
}

export function getMe(token: string) {
  return request<User>('/users/me', {}, token);
}

export function updateMe(token: string, payload: Partial<Pick<User, 'target_language' | 'favorite_langs' | 'preferred_engine' | 'ui_language'>>) {
  return request<User>(
    '/users/me',
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function translateText(token: string, payload: TranslateRequest) {
  return request<TranslateResponse>(
    '/translate',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function getChats(token: string) {
  return request<ChatsResponse>('/chats', {}, token);
}

export function createChat(token: string, payload: Pick<ChatConfig, 'chat_username' | 'source_lang' | 'target_lang'>) {
  return request<ChatConfig>(
    '/chats',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function updateChat(token: string, chatId: number, payload: Partial<Pick<ChatConfig, 'source_lang' | 'target_lang' | 'is_active'>>) {
  return request<ChatConfig>(
    `/chats/${chatId}`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    },
    token,
  );
}

export function deleteChat(token: string, chatId: number) {
  return request<void>(
    `/chats/${chatId}`,
    {
      method: 'DELETE',
    },
    token,
  );
}

export function getStats(token: string) {
  return request<StatsResponse>('/stats/me', {}, token);
}

export function getPlans(token: string) {
  return request<BillingPlansResponse>('/billing/plans', {}, token);
}

export function createCheckout(token: string, planId: string) {
  return request<CheckoutResponse>(
    '/billing/checkout',
    {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId, payment_method: 'telegram_stars' }),
    },
    token,
  );
}

export { API_URL };
