import React from 'react';
import ReactDOM from 'react-dom/client';
import { MantineProvider } from '@mantine/core';
import type { MantineColorScheme, MantineColorSchemeManager } from '@mantine/core';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import '@mantine/core/styles.css';
import '@mantine/charts/styles.css';

import App from './App';
import './styles.css';

const queryClient = new QueryClient();

function currentTgScheme(): MantineColorScheme | undefined {
  const scheme = window.Telegram?.WebApp?.colorScheme;
  return scheme === 'dark' || scheme === 'light' ? scheme : undefined;
}

function applyTelegramTheme() {
  const tg = window.Telegram?.WebApp;
  if (!tg) return;
  const bg = tg.themeParams?.bg_color;
  if (!bg) return;
  let meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', 'theme-color');
    document.head.appendChild(meta);
  }
  meta.setAttribute('content', bg);
  try {
    tg.setHeaderColor(bg);
    tg.setBackgroundColor(bg);
  } catch {
    // older clients
  }
}

/** Mantine color scheme manager backed by the Telegram client theme (no localStorage). */
function telegramColorSchemeManager(fallback: MantineColorScheme): MantineColorSchemeManager {
  return {
    get: () => currentTgScheme() ?? fallback,
    set: () => {
      // controlled by the Telegram client
    },
    subscribe: (onUpdate) => {
      window.Telegram?.WebApp?.onEvent?.('themeChanged', () => {
        const scheme = currentTgScheme();
        if (scheme) {
          onUpdate(scheme);
          applyTelegramTheme();
        }
      });
    },
    unsubscribe: () => {
      // Telegram has no offEvent for themeChanged in older clients; no-op
    },
    clear: () => {
      // nothing to clear
    },
  };
}

applyTelegramTheme();

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MantineProvider defaultColorScheme="light" colorSchemeManager={telegramColorSchemeManager('light')}>
        <App />
      </MantineProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
