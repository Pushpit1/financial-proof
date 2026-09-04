export interface CounterexampleEvent {
  id: string
  sequence: number
  event: string
  occurred_at: string
}

export interface Counterexample {
  simulation_id: string
  violation_code: string
  original_event_count: number
  minimized_event_count: number
  events: CounterexampleEvent[]
}
