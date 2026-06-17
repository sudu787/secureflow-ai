// SecureFlow AI - API Client (Optimized)
// Features: response caching, deduplication, smart error handling

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ─── In-memory response cache ─────────────────────────────────────────────────
const _cache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL: Record<string, number> = {
  '/api/dashboard/full': 10_000,      // 10s — dashboard refreshes often
  '/api/dashboard/stats': 10_000,
  '/api/agents/status': 60_000,       // 60s — agents don't change
  '/api/demo/scenarios': 300_000,     // 5min — static data
  '/api/alerts': 8_000,               // 8s
  '/api/incidents': 10_000,
  '/api/tickets': 10_000,
  '/api/events': 15_000,
  '/api/chat/sessions': 5_000,
};

function getCacheTTL(endpoint: string): number {
  // Match prefix (ignore query params)
  const path = endpoint.split('?')[0];
  return CACHE_TTL[path] || 0;
}

// ─── Request deduplication (prevents duplicate in-flight requests) ─────────────
const _inflight = new Map<string, Promise<any>>();

// ─── Core fetch with caching + dedup ──────────────────────────────────────────
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const method = options?.method || 'GET';
  const cacheKey = `${method}:${endpoint}`;

  // Only cache GET requests
  if (method === 'GET') {
    const ttl = getCacheTTL(endpoint);
    if (ttl > 0) {
      const cached = _cache.get(cacheKey);
      if (cached && Date.now() - cached.timestamp < ttl) {
        return cached.data as T;
      }
    }

    // Deduplicate concurrent identical requests
    if (_inflight.has(cacheKey)) {
      return _inflight.get(cacheKey) as Promise<T>;
    }
  }

  const fetchPromise = (async () => {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${res.status}`);
    }
    const data = await res.json();

    // Cache successful GET responses
    if (method === 'GET') {
      const ttl = getCacheTTL(endpoint);
      if (ttl > 0) {
        _cache.set(cacheKey, { data, timestamp: Date.now() });
      }
    }

    return data;
  })();

  if (method === 'GET') {
    _inflight.set(cacheKey, fetchPromise);
    fetchPromise.finally(() => _inflight.delete(cacheKey));
  }

  return fetchPromise;
}

/** Invalidate cache for a specific endpoint pattern */
export function invalidateCache(pattern?: string) {
  if (!pattern) {
    _cache.clear();
    return;
  }
  for (const key of _cache.keys()) {
    if (key.includes(pattern)) _cache.delete(key);
  }
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
export const getDashboard = () => fetchAPI<any>('/api/dashboard/full');
export const getDashboardStats = () => fetchAPI<any>('/api/dashboard/stats');
export const getSystemHealth = () => fetchAPI<any[]>('/api/dashboard/system-health');
export const getThreatTrends = (hours = 24) => fetchAPI<any[]>(`/api/dashboard/threats?hours=${hours}`);
export const getSeverityDistribution = () => fetchAPI<any>('/api/dashboard/severity-distribution');

// ─── Alerts ───────────────────────────────────────────────────────────────────
export const getAlerts = (params?: { status?: string; severity?: string; limit?: number }) => {
  const qs = new URLSearchParams();
  if (params?.status) qs.set('status', params.status);
  if (params?.severity) qs.set('severity', params.severity);
  if (params?.limit) qs.set('limit', String(params.limit));
  return fetchAPI<any[]>(`/api/alerts?${qs}`);
};
export const getAlert = (id: number) => fetchAPI<any>(`/api/alerts/${id}`);
export const updateAlert = (id: number, data: any) => {
  invalidateCache('/api/alerts');
  return fetchAPI<any>(`/api/alerts/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
};
export const analyzeAlert = (id: number) =>
  fetchAPI<any>(`/api/alerts/${id}/analyze`, { method: 'POST' });

// ─── Incidents ────────────────────────────────────────────────────────────────
export const getIncidents = (params?: { status?: string; limit?: number }) => {
  const qs = new URLSearchParams();
  if (params?.status) qs.set('status', params.status);
  if (params?.limit) qs.set('limit', String(params.limit));
  return fetchAPI<any[]>(`/api/incidents?${qs}`);
};
export const getIncident = (id: number) => fetchAPI<any>(`/api/incidents/${id}`);

// ─── Tickets ──────────────────────────────────────────────────────────────────
export const getTickets = (params?: { status?: string; category?: string; limit?: number }) => {
  const qs = new URLSearchParams();
  if (params?.status) qs.set('status', params.status);
  if (params?.category) qs.set('category', params.category);
  if (params?.limit) qs.set('limit', String(params.limit));
  return fetchAPI<any[]>(`/api/tickets?${qs}`);
};
export const createTicket = (data: any) => {
  invalidateCache('/api/tickets');
  return fetchAPI<any>('/api/tickets', { method: 'POST', body: JSON.stringify(data) });
};
export const updateTicket = (id: number, data: any) => {
  invalidateCache('/api/tickets');
  return fetchAPI<any>(`/api/tickets/${id}`, { method: 'PATCH', body: JSON.stringify(data) });
};

// ─── Chat ─────────────────────────────────────────────────────────────────────
export const sendChatMessage = (message: string, sessionId?: number, sessionType?: string) =>
  fetchAPI<any>('/api/chat/message', {
    method: 'POST',
    body: JSON.stringify({ message, session_id: sessionId, session_type: sessionType }),
  });
export const getChatSessions = () => fetchAPI<any[]>('/api/chat/sessions');
export const getChatSession = (id: number) => fetchAPI<any>(`/api/chat/sessions/${id}`);

// ─── Demo ─────────────────────────────────────────────────────────────────────
export const getDemoScenarios = () => fetchAPI<any[]>('/api/demo/scenarios');
export const startDemoScenario = (id: string) => {
  invalidateCache();  // Demo changes everything
  return fetchAPI<any>(`/api/demo/start/${id}`, { method: 'POST' });
};
export const startAllScenarios = () => {
  invalidateCache();
  return fetchAPI<any>('/api/demo/start-all', { method: 'POST' });
};
export const resetDemo = () => {
  invalidateCache();
  return fetchAPI<any>('/api/demo/reset', { method: 'POST' });
};

// ─── Events ───────────────────────────────────────────────────────────────────
export const getEvents = (params?: { source_type?: string; limit?: number }) => {
  const qs = new URLSearchParams();
  if (params?.source_type) qs.set('source_type', params.source_type);
  if (params?.limit) qs.set('limit', String(params.limit));
  return fetchAPI<any[]>(`/api/events?${qs}`);
};

// ─── Agents ───────────────────────────────────────────────────────────────────
export const getAgentActivity = (limit = 20) =>
  fetchAPI<any[]>(`/api/agents/activity?limit=${limit}`);
export const getAgentStatus = () =>
  fetchAPI<any>('/api/agents/status');

// ─── Health ───────────────────────────────────────────────────────────────────
export const getHealth = () => fetchAPI<any>('/api/health');

// ─── Ingestion ────────────────────────────────────────────────────────────────
export const getIngestionStatus = () => fetchAPI<any>('/api/ingestion/status');
export const startIngestion = () =>
  fetchAPI<any>('/api/ingestion/start', { method: 'POST' });
export const stopIngestion = () =>
  fetchAPI<any>('/api/ingestion/stop', { method: 'POST' });

// ─── Notifications ────────────────────────────────────────────────────────────
export const getNotifications = (limit = 50) =>
  fetchAPI<any[]>(`/api/notifications?limit=${limit}`);
export const getUnreadNotificationCount = () =>
  fetchAPI<{ count: number }>('/api/notifications/unread-count');
export const markNotificationRead = (id: number) =>
  fetchAPI<any>(`/api/notifications/${id}/read`, { method: 'PATCH' });
export const markAllNotificationsRead = () =>
  fetchAPI<any>('/api/notifications/mark-all-read', { method: 'POST' });
