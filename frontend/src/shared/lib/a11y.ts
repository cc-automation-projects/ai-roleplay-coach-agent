// Утилиты для доступности

/**
 * Управление фокусом для модальных окон
 */
export const focusTrap = (element: HTMLElement | null) => {
  if (!element) return;
  const focusable = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  if (focusable.length === 0) return;
  const first = focusable[0] as HTMLElement;
  const last = focusable[focusable.length - 1] as HTMLElement;

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Tab') {
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    }
    if (e.key === 'Escape') {
      // Находим кнопку закрытия
      const closeBtn = element.querySelector('[data-close]') as HTMLElement;
      if (closeBtn) closeBtn.click();
    }
  };

  element.addEventListener('keydown', handleKeyDown);
  return () => element.removeEventListener('keydown', handleKeyDown);
};

/**
 * Анонс для скринридеров (aria-live)
 */
export const announce = (message: string, priority: 'polite' | 'assertive' = 'polite') => {
  const announcer = document.getElementById('a11y-announcer');
  if (!announcer) {
    const div = document.createElement('div');
    div.id = 'a11y-announcer';
    div.setAttribute('aria-live', priority);
    div.setAttribute('aria-atomic', 'true');
    div.className = 'sr-only';
    document.body.appendChild(div);
    div.textContent = message;
    return;
  }
  announcer.textContent = message;
};
