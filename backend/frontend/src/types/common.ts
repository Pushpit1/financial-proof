export interface HealthResponse {
  status: string
}

export interface ReadinessResponse {
  status: string
}

export interface ApiErrorDetail {
  code: string
  message: string
  details: Record<string, unknown>
}

export interface ApiErrorResponse {
  success: false
  error: ApiErrorDetail
}
