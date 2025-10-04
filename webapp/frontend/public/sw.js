/**
 * Service Worker - Offline Capability and Caching
 * Provides offline functionality and performance optimization
 */

const CACHE_NAME = 'secure-rag-system-v1';
const OFFLINE_CACHE = 'offline-rag-system-v1';

// Files to cache for offline use
const STATIC_CACHE_URLS = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/favicon.ico',
];

// API endpoints that can work offline
const OFFLINE_FALLBACK_ENDPOINTS = [
  '/api/health',
  '/api/models',
  '/api/conversations',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_CACHE_URLS);
      })
      .then(() => {
        console.log('Service Worker: Installation complete');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Installation failed', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME && cacheName !== OFFLINE_CACHE) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activation complete');
        return self.clients.claim();
      })
      .catch((error) => {
        console.error('Service Worker: Activation failed', error);
      })
  );
});

// Fetch event - handle requests with caching strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle static assets
  if (isStaticAsset(request)) {
    event.respondWith(handleStaticAsset(request));
    return;
  }

  // Handle navigation requests
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigation(request));
    return;
  }

  // Default: try network first, fall back to cache
  event.respondWith(
    fetch(request)
      .catch(() => caches.match(request))
  );
});

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
  const url = new URL(request.url);

  try {
    // Try network first
    const networkResponse = await fetch(request);

    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(OFFLINE_CACHE);
      cache.put(request.url, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('Service Worker: Network failed, trying cache', url.pathname);

    // Try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline fallback for supported endpoints
    if (OFFLINE_FALLBACK_ENDPOINTS.some(endpoint => url.pathname.startsWith(endpoint))) {
      return getOfflineFallback(url.pathname);
    }

    // Return generic offline response
    return new Response(
      JSON.stringify({
        success: false,
        message: 'Offline - This feature requires an internet connection',
        offline: true,
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  }
}

// Handle static assets with cache-first strategy
async function handleStaticAsset(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  try {
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request.url, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('Service Worker: Failed to fetch static asset', request.url);
    throw error;
  }
}

// Handle navigation requests
async function handleNavigation(request) {
  try {
    return await fetch(request);
  } catch (error) {
    // Return cached index.html for offline SPA navigation
    const cachedResponse = await caches.match('/');
    if (cachedResponse) {
      return cachedResponse;
    }

    // Return offline page
    return new Response(`
      <!DOCTYPE html>
      <html>
        <head>
          <title>Offline - Secure RAG System</title>
          <meta charset="utf-8">
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            body {
              font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
              display: flex;
              align-items: center;
              justify-content: center;
              min-height: 100vh;
              margin: 0;
              background: #f5f5f5;
            }
            .offline-container {
              text-align: center;
              padding: 2rem;
              background: white;
              border-radius: 8px;
              box-shadow: 0 2px 10px rgba(0,0,0,0.1);
              max-width: 400px;
            }
            .offline-icon {
              font-size: 64px;
              color: #666;
              margin-bottom: 1rem;
            }
            .retry-button {
              background: #1976d2;
              color: white;
              border: none;
              padding: 12px 24px;
              border-radius: 4px;
              cursor: pointer;
              font-size: 16px;
              margin-top: 1rem;
            }
          </style>
        </head>
        <body>
          <div class="offline-container">
            <div class="offline-icon">📡</div>
            <h1>You're Offline</h1>
            <p>The Secure RAG System is temporarily unavailable. Please check your connection and try again.</p>
            <button class="retry-button" onclick="window.location.reload()">
              Retry
            </button>
          </div>
        </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    });
  }
}

// Get offline fallback responses
function getOfflineFallback(pathname) {
  const fallbacks = {
    '/api/health': {
      success: true,
      data: {
        status: 'offline',
        version: '1.0.0',
        security_mode: 'local_only',
        offline: true,
      },
      message: 'Health check (offline mode)',
    },
    '/api/models': {
      success: true,
      data: ['mistral', 'llama2', 'codellama'],
      message: 'Models retrieved (offline cache)',
    },
    '/api/conversations': {
      success: true,
      data: JSON.parse(localStorage.getItem('cachedConversations') || '[]'),
      message: 'Conversations retrieved (offline cache)',
    },
  };

  const fallback = Object.keys(fallbacks).find(key => pathname.startsWith(key));
  if (fallback) {
    return new Response(
      JSON.stringify(fallbacks[fallback]),
      {
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }

  return null;
}

// Check if request is for a static asset
function isStaticAsset(request) {
  const url = new URL(request.url);
  return (
    url.pathname.startsWith('/static/') ||
    url.pathname.endsWith('.js') ||
    url.pathname.endsWith('.css') ||
    url.pathname.endsWith('.png') ||
    url.pathname.endsWith('.jpg') ||
    url.pathname.endsWith('.svg') ||
    url.pathname.endsWith('.ico') ||
    url.pathname === '/manifest.json'
  );
}

// Message handling for cache management
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => caches.delete(cacheName))
      );
    }).then(() => {
      event.ports[0].postMessage({ success: true });
    });
  }

  if (event.data && event.data.type === 'CACHE_CONVERSATIONS') {
    // Cache conversations for offline access
    localStorage.setItem('cachedConversations', JSON.stringify(event.data.conversations));
  }
});

// Background sync for queued actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync-messages') {
    event.waitUntil(processQueuedMessages());
  }
});

// Process queued messages when back online
async function processQueuedMessages() {
  const queuedMessages = JSON.parse(localStorage.getItem('queuedMessages') || '[]');

  for (const message of queuedMessages) {
    try {
      const response = await fetch('/api/chat/message', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(message),
      });

      if (response.ok) {
        // Remove from queue
        const index = queuedMessages.indexOf(message);
        queuedMessages.splice(index, 1);
        localStorage.setItem('queuedMessages', JSON.stringify(queuedMessages));

        // Notify client
        self.clients.matchAll().then((clients) => {
          clients.forEach((client) => {
            client.postMessage({
              type: 'MESSAGE_SENT',
              message: message,
            });
          });
        });
      }
    } catch (error) {
      console.error('Failed to send queued message:', error);
    }
  }
}

console.log('Service Worker: Loaded and ready');