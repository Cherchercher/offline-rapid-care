const CACHE_NAME = 'rapidcare-v1';
const OFFLINE_URL = '/offline.html';
const urlsToCache = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/manifest.json',
    '/static/images/icon-192x192.png',
    '/static/images/icon-512x512.png',
    OFFLINE_URL
];

// Install event - cache resources
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached version or fetch from network
                if (response) {
                    return response;
                }
                
                return fetch(event.request).then(
                    (response) => {
                        // Check if we received a valid response
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response
                        const responseToCache = response.clone();

                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    }
                );
            })
            .catch(() => {
                // Return offline page for navigation requests
                if (event.request.mode === 'navigate') {
                    return caches.match(OFFLINE_URL);
                }
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    try {
        // Get stored offline actions
        const offlineActions = await getOfflineActions();
        
        for (const action of offlineActions) {
            try {
                // Retry the action
                const response = await fetch(action.url, {
                    method: action.method,
                    headers: action.headers,
                    body: action.body
                });
                
                if (response.ok) {
                    // Remove from offline storage if successful
                    await removeOfflineAction(action.id);
                }
            } catch (error) {
                console.error('Background sync failed for action:', action.id, error);
            }
        }
    } catch (error) {
        console.error('Background sync error:', error);
    }
}

// Store offline actions
async function storeOfflineAction(action) {
    const db = await openDB();
    const tx = db.transaction('offlineActions', 'readwrite');
    const store = tx.objectStore('offlineActions');
    await store.add(action);
}

// Get stored offline actions
async function getOfflineActions() {
    const db = await openDB();
    const tx = db.transaction('offlineActions', 'readonly');
    const store = tx.objectStore('offlineActions');
    return await store.getAll();
}

// Remove offline action
async function removeOfflineAction(id) {
    const db = await openDB();
    const tx = db.transaction('offlineActions', 'readwrite');
    const store = tx.objectStore('offlineActions');
    await store.delete(id);
}

// Open IndexedDB
async function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('RapidCareDB', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            // Create object store for offline actions
            if (!db.objectStoreNames.contains('offlineActions')) {
                const store = db.createObjectStore('offlineActions', { keyPath: 'id', autoIncrement: true });
                store.createIndex('timestamp', 'timestamp', { unique: false });
            }
        };
    });
}

// Push notification handling
self.addEventListener('push', (event) => {
    const options = {
        body: event.data ? event.data.text() : 'New message from RapidCare',
        icon: '/static/images/icon-192x192.png',
        badge: '/static/images/icon-192x192.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'View',
                icon: '/static/images/icon-192x192.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/images/icon-192x192.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('RapidCare', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
}); 