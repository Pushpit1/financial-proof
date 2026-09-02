import { apiClient } from './client'
import type {
  VerificationRequest,
  VerificationResponse,
} from '../types/verification'

export function verifySnapshots(
  request: VerificationRequest,
): Promise<VerificationResponse> {
  return apiClient.post<VerificationResponse>(
    '/verification',
    request,
  )
}
