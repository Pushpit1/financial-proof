const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') || '/api'

export function getAuthToken(): string {
  if (typeof window === 'undefined') return ''
  return window.localStorage.getItem('fp_bearer_token') || ''
}

export function setAuthToken(token: string): void {
  if (typeof window === 'undefined') return
  const clean = token.trim()
  if (clean) {
    window.localStorage.setItem('fp_bearer_token', clean)
  } else {
    window.localStorage.removeItem('fp_bearer_token')
  }
}

export class ApiClientError extends Error {
  readonly status: number
  readonly details: unknown

  constructor(status: number, message: string, details?: unknown) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.details = details
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  const token = getAuthToken()
  const isFormData =
    typeof FormData !== 'undefined' && init?.body instanceof FormData

  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...(!isFormData && init?.body ? { 'Content-Type': 'application/json' } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((init?.headers as Record<string, string> | undefined) || {}),
  }

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
    })
  } catch (error) {
    throw new ApiClientError(
      0,
      'Unable to connect to the Financial Proof backend.',
      error,
    )
  }

  const text = await response.text()
  let payload: unknown = null

  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = text
    }
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}.`
    if (typeof payload === 'object' && payload !== null) {
      if ('detail' in payload && typeof payload.detail === 'string') {
        message = payload.detail
      } else if (
        'error' in payload &&
        typeof payload.error === 'object' &&
        payload.error !== null &&
        'message' in payload.error &&
        typeof payload.error.message === 'string'
      ) {
        message = payload.error.message
      }
    }
    throw new ApiClientError(response.status, message, payload)
  }

  return payload as T
}

export const apiClient = {
  get<T>(path: string): Promise<T> {
    return request<T>(path)
  },

  post<T>(path: string, body: unknown): Promise<T> {
    return request<T>(path, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  upload<T>(path: string, formData: FormData): Promise<T> {
    return request<T>(path, {
      method: 'POST',
      body: formData,
    })
  },

  async getText(path: string): Promise<string> {
    const token = getAuthToken()
    const res = await fetch(`${API_BASE_URL}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    })
    if (!res.ok) {
      throw new ApiClientError(res.status, `Export failed (${res.status})`)
    }
    return res.text()
  },
}
