// frontend/src/hooks/useToast.ts
import { useCallback } from 'react';

type ToastOpts = { duration?: number };
type ToastApi = {
  success: (message: string, opts?: ToastOpts) => void;
  error: (message: string, opts?: ToastOpts) => void;
  info?: (message: string, opts?: ToastOpts) => void;
};

const CONTAINER_ID = 'app-toast-container';

function ensureContainer(): HTMLDivElement | null {
  if (typeof window === 'undefined') return null;
  let container = document.getElementById(CONTAINER_ID) as HTMLDivElement | null;
  if (!container) {
    container = document.createElement('div');
    container.id = CONTAINER_ID;
    // Basic positioning/styling so toasts are visible without external CSS
    Object.assign(container.style, {
      position: 'fixed',
      top: '20px',
      right: '20px',
      zIndex: '9999',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px',
      alignItems: 'flex-end'
    });
    document.body.appendChild(container);
  }
  return container;
}

function createToastEl(message: string, type: 'success' | 'error' | 'info') {
  const el = document.createElement('div');
  Object.assign(el.style, {
    minWidth: '200px',
    maxWidth: '360px',
    padding: '10px 14px',
    color: '#fff',
    background: type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#17a2b8',
    borderRadius: '6px',
    boxShadow: '0 6px 18px rgba(0,0,0,0.12)',
    opacity: '0',
    transform: 'translateY(-6px)',
    transition: 'opacity 240ms ease, transform 240ms ease',
    cursor: 'pointer',
    fontSize: '14px',
    lineHeight: '1.2',
    wordBreak: 'break-word'
  });
  el.textContent = message;
  return el;
}

function showToast(message: string, type: 'success' | 'error' | 'info' = 'info', duration = 5000) {
  const container = ensureContainer();
  if (!container) return;

  const toastEl = createToastEl(message, type);
  container.appendChild(toastEl);

  // trigger enter animation
  requestAnimationFrame(() => {
    toastEl.style.opacity = '1';
    toastEl.style.transform = 'translateY(0)';
  });

  const remove = () => {
    if (!toastEl.parentElement) return;
    toastEl.style.opacity = '0';
    toastEl.style.transform = 'translateY(-6px)';
    // wait for animation
    setTimeout(() => {
      toastEl.remove();
      // if container is empty remove it to keep DOM clean
      if (container && container.childElementCount === 0) {
        container.remove();
      }
    }, 260);
  };

  // auto remove
  const timeoutId = window.setTimeout(remove, duration);

  // remove on click
  toastEl.addEventListener('click', () => {
    clearTimeout(timeoutId);
    remove();
  });
}

export const useToast = (): ToastApi => {
  const success = useCallback((message: string, opts?: ToastOpts) => {
    showToast(message, 'success', opts?.duration ?? 4000);
  }, []);

  const error = useCallback((message: string, opts?: ToastOpts) => {
    showToast(message, 'error', opts?.duration ?? 6000);
  }, []);

  const info = useCallback((message: string, opts?: ToastOpts) => {
    showToast(message, 'info', opts?.duration ?? 4000);
  }, []);

  return { success, error, info };
};