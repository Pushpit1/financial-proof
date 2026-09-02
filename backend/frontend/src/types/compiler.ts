export interface FinancialContractCompileRequest {
  source_text: string
}

export interface FinancialContractCompileContract {
  id: string
  name: string
  version: number
  minimum_confidence: number
  minimum_supported_claim_ratio: number
  required_claim_types: string[]
}

export interface FinancialContractCompileResponse {
  source_text: string
  contract: FinancialContractCompileContract
}
