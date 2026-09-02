export interface SimulationEventRequest {
  event: string
  occurred_at: string
}

export interface SimulationCreateRequest {
  seed: number
  amount_minor: number
  currency: string
  events: SimulationEventRequest[]
}

export interface SimulationEvent {
  id: string
  sequence: number
  event: string
  occurred_at: string
}

export interface SimulationTraceEntry {
  sequence: number
  event: string
  occurred_at: string
}

export interface SimulationState {
  payment_state: string
  order_state: string
}

export interface SimulationResult {
  simulation_id: string
  seed: number
  final_payment_state: string
  final_order_state: string
  trace: SimulationTraceEntry[]
  snapshots: SimulationState[]
}

export interface Simulation {
  id: string
  seed: number
  amount_minor: number
  currency: string
  events: SimulationEvent[]
  result: SimulationResult
}

export interface AttackRequest {
  attack_type: string
  target_sequence: number
  retry_count?: number
  delay_seconds?: number
  worker_sequence?: number
  incoming_sequence?: number
}

export interface AttackOutcome {
  component_type: string
  target_sequence: number
  status: string
}

export interface AdversarialSimulation {
  simulation_id: string
  attack_count: number
  applied_components: string[]
  outcomes: AttackOutcome[]
  baseline: SimulationResult
  adversarial: SimulationResult
}
