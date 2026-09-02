export interface VerificationSnapshotRequest {
  contract_id?: string
  contract_version: string
  system_version: string
  baseline: Record<string, unknown>
  violations: string[]
  counterexample_ids: string[]
  simulation_id?: string
  reproducibility_metadata: Record<string, unknown>
}

export interface VerificationRequest {
  before: VerificationSnapshotRequest
  after: VerificationSnapshotRequest
}

export interface VerificationChange {
  field: string
  before: unknown
  after: unknown
  change_type: string
}

export interface VerificationSnapshot {
  snapshot_id: string
  created_at: string
  contract_id: string | null
  contract_version: string
  system_version: string
  baseline: Record<string, unknown>
  violations: string[]
  counterexample_ids: string[]
  simulation_id: string | null
  reproducibility_metadata: Record<string, unknown>
}

export interface VerificationComparison {
  comparison_id: string
  before_snapshot_id: string
  after_snapshot_id: string
  contract_version_changed: boolean
  system_version_changed: boolean
  changes: VerificationChange[]
  added_changes: string[]
  removed_changes: string[]
  introduced_violations: string[]
  resolved_violations: string[]
  added_counterexample_ids: string[]
  removed_counterexample_ids: string[]
  regression_detected: boolean
}

export interface VerificationResult {
  verification_id: string
  before_snapshot_id: string
  after_snapshot_id: string
  comparison_id: string
  passed: boolean
  regression_detected: boolean
  violations: string[]
  reproducible: boolean
}

export interface VerificationResponse {
  result: VerificationResult
  before: VerificationSnapshot
  after: VerificationSnapshot
  comparison: VerificationComparison
}
