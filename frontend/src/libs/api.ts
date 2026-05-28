// API client

import type { DiscoveryResponse, DiscoveryListItem, DiscoveryQueryParams, SavedLocation, PlanningWeather, User } from '@/types'

export class ApiError extends Error {
    status: number

    constructor(status: number, message: string) {
        super(message)
        this.status = status
    }
}

let _getAccessToken: () => string | null = () => null
let _refreshToken: () => Promise<void> = async () => {}

export function configureTokenGetter(getter: () => string | null) {
    _getAccessToken = getter
}

export function configureRefreshHandler(refresher: () => Promise<void>) {
    _refreshToken = refresher
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const access_token = _getAccessToken()

    const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...(access_token ? { 'Authorization': `Bearer ${access_token}` } : {}),
    }

    const response = await fetch('/api' + path, { ...options, headers })

    if (response.status === 401 && !path.includes('/auth/refresh')) {
        await _refreshToken()
        const retried_token = _getAccessToken()
        const retried_headers: HeadersInit = {
            'Content-Type': 'application/json',
            ...(retried_token ? { 'Authorization': `Bearer ${retried_token}` } : {}),
        }
        const retried_response = await fetch('/api' + path, { ...options, headers: retried_headers })
        if (!retried_response.ok) {
            const errorText = await retried_response.text()
            throw new ApiError(retried_response.status, errorText)
        }
        if (retried_response.status === 204) return undefined as T
        return retried_response.json() as Promise<T>
    }

    if (response.status === 429) {
        throw new ApiError(429, "Too many requests. Please wait and try again.")
    }

    if (!response.ok) {
        const errorText = await response.text()
        throw new ApiError(response.status, errorText)
    }

    if (response.status === 204) {
        return undefined as T
    }

    return response.json() as Promise<T>
}

export const api = {
    get: <T>(path: string) => request<T>(path, { method: 'GET' }),
    post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
    put: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
    patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body: JSON.stringify(body) }),
    delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
    getDiscoveries: (params: DiscoveryQueryParams = {}) => {
        const searchParams = new URLSearchParams()
        searchParams.set('limit', String(params.limit ?? 20))
        if (params.cursor) searchParams.set('cursor', params.cursor)
        if (params.q) searchParams.set('q', params.q)
        if (params.safety) searchParams.set('safety', params.safety)
        if (params.confidence_min != null) searchParams.set('confidence_min', String(params.confidence_min))
        if (params.confidence_max != null) searchParams.set('confidence_max', String(params.confidence_max))
        if (params.date_from) searchParams.set('date_from', params.date_from)
        if (params.date_to) searchParams.set('date_to', params.date_to)
        return request<DiscoveryListItem[]>(`/discoveries?${searchParams.toString()}`, { method: 'GET' })
    },
    getDiscovery: (id: string) =>
        request<DiscoveryResponse>(`/discoveries/${id}`, { method: 'GET' }),
    updateDiscovery: (id: string, userNotes: string) =>
        request<DiscoveryResponse>(`/discoveries/${id}`, { method: 'PATCH', body: JSON.stringify({ user_notes: userNotes }) }),
    deleteDiscovery: (id: string) =>
        request(`/discoveries/${id}`, { method: 'DELETE' }),
    updateProfile: (data: { display_name?: string; default_location?: { city?: string; state?: string } }) =>
        request<User>('/auth/me', { method: 'PATCH', body: JSON.stringify(data) }),

    // Locations
    getLocations: () =>
        request<SavedLocation[]>('/locations', { method: 'GET' }),
    createLocation: (data: { label: string; city?: string; state?: string; zip_code?: string; latitude?: number; longitude?: number }) =>
        request<SavedLocation>('/locations', { method: 'POST', body: JSON.stringify(data) }),
    pinLocation: (id: string) =>
        request<SavedLocation>(`/locations/${id}/pin`, { method: 'PATCH' }),
    deleteLocation: (id: string) =>
        request(`/locations/${id}`, { method: 'DELETE' }),

    // Weather
    getPlanningWeather: (lat: number, lng: number) =>
        request<PlanningWeather>(`/weather/planning?lat=${lat}&lng=${lng}`, { method: 'GET' }),
}
