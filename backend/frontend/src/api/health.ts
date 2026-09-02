import { apiClient } from './client'
import type { HealthResponse, ReadinessResponse } from '../types/common'

export function getHealth(): Promise<HealthResponse> {
  return apiClient.get<HealthResponse>('/health')
}

export function getReadiness(): Promise<ReadinessResponse> {
  return apiClient.get<ReadinessResponse>('/ready')
}
