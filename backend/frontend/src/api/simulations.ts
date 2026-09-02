import { apiClient } from './client'
import type {
  AdversarialSimulation,
  AttackRequest,
  Simulation,
  SimulationCreateRequest,
} from '../types/simulation'

export function createSimulation(
  request: SimulationCreateRequest,
): Promise<Simulation> {
  return apiClient.post<Simulation>('/simulations', request)
}

export function getSimulation(
  simulationId: string,
): Promise<Simulation> {
  return apiClient.get<Simulation>(
    `/simulations/${simulationId}`,
  )
}

export function executeAttack(
  simulationId: string,
  request: AttackRequest,
): Promise<AdversarialSimulation> {
  return apiClient.post<AdversarialSimulation>(
    `/simulations/${simulationId}/attacks`,
    request,
  )
}
