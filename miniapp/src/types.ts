export type TranslationEngine = 'auto' | 'google_free' | 'deepl';

export interface AuthRequest {
  init_data: string;
}

export interface User {
  id: number;
  telegram_id_hash?: string;
  username?: string | null;
  target_language: string;
  favorite_langs: string[];
  preferred_engine: TranslationEngine;
  ui_language: string;
  plan: string;
  chars_limit: number;
  chars_used: number;
  chars_remaining: number;
  reset_at: string | null;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  is_new: boolean;
  user: User;
}

export interface TranslateRequest {
  text: string;
  source_lang: string;
  target_lang: string;
  context?: string;
  engine?: TranslationEngine;
}

export interface TranslateResponse {
  translated_text: string;
  source_lang_detected: string;
  target_lang: string;
  provider: string;
  cached: boolean;
  char_count: number;
  chars_remaining: number;
}

export interface ChatConfig {
  id: number;
  chat_id: number;
  chat_title?: string | null;
  chat_username?: string | null;
  source_lang: string;
  target_lang: string;
  is_active: boolean;
  last_synced_at?: string | null;
}

export interface ChatsResponse {
  items: ChatConfig[];
  total: number;
  limit_reached: boolean;
  max_chats: number;
}

export interface StatsPoint {
  date: string;
  chars: number;
}

export interface StatsResponse {
  period: string;
  total_chars: number;
  total_requests: number;
  chars_by_day: StatsPoint[];
  top_languages: Array<{ lang: string; chars: number }>;
  providers_used: Record<string, number>;
}

export interface BillingPlan {
  id: string;
  name: string;
  chars_per_month: number;
  price_usd: number;
  price_stars: number;
  max_auto_chats: number;
  features: string[];
}

export interface BillingPlansResponse {
  plans: BillingPlan[];
  current_plan: string;
}

export interface CheckoutResponse {
  invoice_url: string;
  expires_at: string;
}
