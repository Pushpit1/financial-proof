const API_BASE_URL = '/api'

export class ApiClientError extends Error {
  readonly status: number
  readonly details: unknown

  constructor(
    status: number,
    message: string,
    details?: unknown,
  ) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.details = details
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  let response: Response

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init?.body
          ? { 'Content-Type': 'application/json' }
          : {}),
        ...init?.headers,
      },
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
    const message =
      typeof payload === 'object' &&
      payload !== null &&
      'detail' in payload &&
      typeof payload.detail === 'string'
        ? payload.detail
        : `Request failed with status ${response.status}.`

    throw new ApiClientError(
      response.status,
      message,
      payload,
    )
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
}
