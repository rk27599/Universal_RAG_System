/**
 * Service Worker Registration and Management
 * Handles offline capabilities and caching strategies
 */

interface ServiceWorkerConfig {
  onSuccess?: (registration: ServiceWorkerRegistration) => void;
  onUpdate?: (registration: ServiceWorkerRegistration) => void;
  onOffline?: () => void;
  onOnline?: () => void;
}

const isLocalhost = Boolean(
  window.location.hostname === 'localhost' ||
  window.location.hostname === '[::1]' ||
  window.location.hostname.match(/^127(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$/)
);

export function register(config?: ServiceWorkerConfig) {
  if ('serviceWorker' in navigator) {
    const publicUrl = new URL(process.env.PUBLIC_URL || '', window.location.href);
    if (publicUrl.origin !== window.location.origin) {
      return;
    }

    window.addEventListener('load', () => {
      const swUrl = `${process.env.PUBLIC_URL}/sw.js`;

      if (isLocalhost) {
        checkValidServiceWorker(swUrl, config);
        navigator.serviceWorker.ready.then(() => {
          console.log('Service worker ready in localhost mode');
        });
      } else {
        registerValidSW(swUrl, config);
      }

      // Register online/offline listeners
      registerNetworkListeners(config);
    });
  }
}

function registerValidSW(swUrl: string, config?: ServiceWorkerConfig) {
  navigator.serviceWorker
    .register(swUrl)
    .then((registration) => {
      console.log('Service Worker registered:', registration);

      registration.onupdatefound = () => {
        const installingWorker = registration.installing;
        if (installingWorker == null) {
          return;
        }

        installingWorker.onstatechange = () => {
          if (installingWorker.state === 'installed') {
            if (navigator.serviceWorker.controller) {
              console.log('New content available, please refresh.');
              if (config?.onUpdate) {
                config.onUpdate(registration);
              }
            } else {
              console.log('Content cached for offline use.');
              if (config?.onSuccess) {
                config.onSuccess(registration);
              }
            }
          }
        };
      };
    })
    .catch((error) => {
      console.error('Service Worker registration failed:', error);
    });
}

function checkValidServiceWorker(swUrl: string, config?: ServiceWorkerConfig) {
  fetch(swUrl, {
    headers: { 'Service-Worker': 'script' },
  })
    .then((response) => {
      const contentType = response.headers.get('content-type');
      if (
        response.status === 404 ||
        (contentType != null && contentType.indexOf('javascript') === -1)
      ) {
        navigator.serviceWorker.ready.then((registration) => {
          registration.unregister().then(() => {
            window.location.reload();
          });
        });
      } else {
        registerValidSW(swUrl, config);
      }
    })
    .catch(() => {
      console.log('No internet connection. App is running in offline mode.');
    });
}

function registerNetworkListeners(config?: ServiceWorkerConfig) {
  window.addEventListener('online', () => {
    console.log('Network: Back online');
    showNetworkStatus(true);
    if (config?.onOnline) {
      config.onOnline();
    }

    // Process any queued actions
    if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        type: 'NETWORK_ONLINE',
      });
    }
  });

  window.addEventListener('offline', () => {
    console.log('Network: Gone offline');
    showNetworkStatus(false);
    if (config?.onOffline) {
      config.onOffline();
    }
  });

  // Initial network status
  showNetworkStatus(navigator.onLine);
}

function showNetworkStatus(isOnline: boolean) {
  // Store network status in localStorage for components to access
  localStorage.setItem('networkStatus', isOnline ? 'online' : 'offline');

  // Dispatch custom event for components to listen to
  window.dispatchEvent(new CustomEvent('networkStatusChange', {
    detail: { isOnline }
  }));
}

export function unregister() {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then((registration) => {
        registration.unregister();
      })
      .catch((error) => {
        console.error(error.message);
      });
  }
}

// Utility functions for service worker communication
export class ServiceWorkerManager {
  private static instance: ServiceWorkerManager;

  static getInstance(): ServiceWorkerManager {
    if (!ServiceWorkerManager.instance) {
      ServiceWorkerManager.instance = new ServiceWorkerManager();
    }
    return ServiceWorkerManager.instance;
  }

  // Send message to service worker
  sendMessage(message: any): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!navigator.serviceWorker.controller) {
        reject(new Error('No service worker controller'));
        return;
      }

      const messageChannel = new MessageChannel();
      messageChannel.port1.onmessage = (event) => {
        resolve(event.data);
      };

      navigator.serviceWorker.controller.postMessage(message, [messageChannel.port2]);
    });
  }

  // Clear all caches
  async clearCache(): Promise<boolean> {
    try {
      await this.sendMessage({ type: 'CLEAR_CACHE' });
      return true;
    } catch (error) {
      console.error('Failed to clear cache:', error);
      return false;
    }
  }

  // Cache conversations for offline access
  cacheConversations(conversations: any[]): void {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({
        type: 'CACHE_CONVERSATIONS',
        conversations,
      });
    }
  }

  // Queue message for background sync
  queueMessage(message: any): void {
    const queuedMessages = JSON.parse(localStorage.getItem('queuedMessages') || '[]');
    queuedMessages.push({
      ...message,
      timestamp: Date.now(),
    });
    localStorage.setItem('queuedMessages', JSON.stringify(queuedMessages));

    // Request background sync
    if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
      navigator.serviceWorker.ready.then((registration) => {
        // TypeScript doesn't know about sync API, so we cast it
        const syncRegistration = registration as any;
        if (syncRegistration.sync) {
          return syncRegistration.sync.register('background-sync-messages');
        }
      });
    }
  }

  // Get network status
  isOnline(): boolean {
    return navigator.onLine;
  }

  // Listen for service worker messages
  listenForMessages(callback: (message: any) => void): () => void {
    const handleMessage = (event: MessageEvent) => {
      callback(event.data);
    };

    navigator.serviceWorker.addEventListener('message', handleMessage);

    return () => {
      navigator.serviceWorker.removeEventListener('message', handleMessage);
    };
  }

  // Force service worker update
  async forceUpdate(): Promise<void> {
    if ('serviceWorker' in navigator) {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration) {
        await registration.update();
      }
    }
  }

  // Skip waiting and activate new service worker
  skipWaiting(): void {
    if (navigator.serviceWorker.controller) {
      navigator.serviceWorker.controller.postMessage({ type: 'SKIP_WAITING' });
    }
  }
}

export default ServiceWorkerManager;