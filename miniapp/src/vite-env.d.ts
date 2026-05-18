/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
  /** Raw Telegram WebApp initData (browser dev only; must be a valid signed string). */
  readonly VITE_DEV_TOKEN?: string;
}
