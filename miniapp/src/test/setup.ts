import '@testing-library/jest-dom';

// Mock ResizeObserver (required by Mantine)
class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
window.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;

// Mock window.matchMedia (required by Mantine)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Mock Telegram WebApp
Object.defineProperty(window, 'Telegram', {
  value: {
    WebApp: {
      initData: 'query_id=test&user=%7B%22id%22%3A123%2C%22first_name%22%3A%22Test%22%7D&auth_date=1&hash=test',
      initDataUnsafe: {
        user: {
          id: 123,
          first_name: 'Test',
          language_code: 'en',
        },
      },
      ready: () => {},
      expand: () => {},
      openTelegramLink: () => {},
      openLink: () => {},
      close: () => {},
      MainButton: {
        setText: () => {},
        show: () => {},
        hide: () => {},
        enable: () => {},
        disable: () => {},
        onClick: () => {},
      },
      BackButton: {
        show: () => {},
        hide: () => {},
        onClick: () => {},
      },
    },
  },
  writable: true,
});
