import { apiClient } from './client'
import type { Counterexample } from '../types/counterexample'

export function shrinkCounterexample(
  simulationId: string,
  attackRequest: {
    attack_type: string
    target_sequence: number
    source_sequence?: number
    retry_count?: number
    delay_seconds?: number
    worker_sequence?: number
    incoming_sequence?: number
  },
): Promise<Counterexample> {
  return apiClient.post<Counterexample>(
    `/simulations/${simulationId}/counterexample`,
    attackRequest,
  )
}
