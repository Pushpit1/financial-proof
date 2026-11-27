import { apiClient } from './client'
import type { FinancialContract } from '../types/contract'

export interface SystemStatus {
  app: string
  version: string
  environment: string
  database: 'connected' | 'unreachable'
  database_error_type: string | null
  schema_ready?: boolean
  missing_tables?: string[]
  alembic_revision?: string | null
  auth_configured: boolean
  metrics: {
    counters: Record<string, number>
    histograms: Record<string, unknown>
  }
}

export interface BlastRadiusResult {
  analysis_id: string
  persisted: boolean
  passed: boolean
  violation_count: number
  total_direct_loss: string
  total_actual_exposure: string
  total_maximum_exposure: string
  currency: string
  exposures: Array<{
    id: string
    source_violation_id: string | null
    field: string | null
    amount: string
    currency: string | null
    explanation: string
    direct_loss: string
    actual_exposure: string
    maximum_exposure: string
  }>
}

export interface InvestigationResponse {
  investigation_id: string
  ai_advisory_only: boolean
  overrides_deterministic_verification: boolean
  summary: string
  root_cause_hypothesis: string
  recommended_actions: string[]
  tool_results: Array<{
    tool: string
    status: string
    explanation: string
    data: Record<string, unknown>
  }>
  audit_record_count: number
}

export interface GuardianEvaluateResponse {
  decision: 'allow' | 'block' | 'review'
  rule: string
  reason: string
  persisted: boolean
  audit_id: string | null
  created_at: string | null
}

export interface GuardianAuditRecord {
  id: string
  actor_id: string | null
  operation: string
  rule: string
  decision: string
  reason: string
  created_at: string
}

export interface AuditEvent {
  id: string
  category: string
  action: string
  summary: string
  created_at: string
}

export interface DocumentUploadResponse {
  evidence_id: string
  filename: string
  extension: string
  size_bytes: number
  checksum_sha256: string
  duplicate_checksum_detected: boolean
  persisted: boolean
  proof_id: string | null
  extracted_row_count: number
  total_amount: string
  extraction_confidence: string
  extracted_rows: Array<{
    row_index: number
    reference: string | null
    amount: string
    currency: string
    status: string | null
  }>
  warnings: string[]
}

export interface DocumentItem {
  id: string
  evidence_type: string
  source_name: string
  received_at: string
  proof_id: string | null
  status: string
  checksum: string | null
  source_reference: string | null
}

export interface ReconciliationResponse {
  reconciliation_id: string
  matched_count: number
  discrepancy_count: number
  total_exposure: string
  discrepancies: Array<{
    discrepancy_type: string
    reference: string
    expected: string
    actual: string
    exposure: string
  }>
}

export interface AuthStatus {
  auth_configured: boolean
  authenticated: boolean
  subject: string | null
  role: string | null
}

export const platformApi = {
  systemStatus: () => apiClient.get<SystemStatus>('/system/status'),
  listContracts: () => apiClient.get<FinancialContract[]>('/contracts'),
  analyzeBlastRadius: (body: {
    contract_id?: string
    source_text?: string
    payment_amount: string
    refund_amount: string
    currency: string
    persist: boolean
  }) => apiClient.post<BlastRadiusResult>('/blast-radius', body),
  listBlastRadius: () => apiClient.get<BlastRadiusResult[]>('/blast-radius'),
  runInvestigation: (body: {
    contract_id?: string
    simulation_id?: string
    violation_summary: string
  }) => apiClient.post<InvestigationResponse>('/investigations', body),
  evaluateGuardian: (body: {
    operation: string
    actor_id: string
    amount_minor: number
    payment_amount_minor: number
    currency: string
    actor_authorized: boolean
    operation_authorized: boolean
    duplicate_detected: boolean
    state_transition_valid: boolean
    requires_manual_review: boolean
    persist_audit: boolean
  }) => apiClient.post<GuardianEvaluateResponse>('/guardian/evaluate', body),
  listGuardianAudit: () => apiClient.get<GuardianAuditRecord[]>('/guardian/audit'),
  listAudit: (category?: string) =>
    apiClient.get<AuditEvent[]>(
      category ? `/audit?category=${encodeURIComponent(category)}` : '/audit',
    ),
  authStatus: () => apiClient.get<AuthStatus>('/auth/status'),
  uploadDocument: (formData: FormData) =>
    apiClient.upload<DocumentUploadResponse>('/documents/upload', formData),
  listDocuments: () => apiClient.get<DocumentItem[]>('/documents'),
  runReconciliation: (body: {
    internal_records: Array<{
      reference: string
      amount: string
      currency: string
      status: string
    }>
    provider_records: Array<{
      reference: string
      amount: string
      currency: string
      status: string
    }>
  }) => apiClient.post<ReconciliationResponse>('/reconciliation/run', body),
  exportProofReport: (proofId: string, format: 'json' | 'csv' | 'markdown') =>
    apiClient.getText(`/proofs/${proofId}/report?format=${format}`),
  listProofsBySubject: (subject: string) =>
    apiClient.get<Array<{ id: string; subject: string; status: string; overall_confidence: string }>>(
      `/proofs?subject=${encodeURIComponent(subject)}`,
    ),
}
