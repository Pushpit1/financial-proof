export interface FinancialContractCreateRequest {
  id?: string
  name: string
  version: number
  minimum_confidence: number
  minimum_supported_claim_ratio: number
  required_claim_types: string[]
}

export interface FinancialContract {
  id: string
  name: string
  version: number
  minimum_confidence: number
  minimum_supported_claim_ratio: number
  required_claim_types: string[]
}

export interface FinancialContractDecisionEvaluateRequest {
  context: Record<string, unknown>
}

export interface FinancialContractDecision {
  id: string
  contract_id: string
  passed: boolean
  reason_codes: string[]
  violation_count: number
  evaluated_at: string
}
