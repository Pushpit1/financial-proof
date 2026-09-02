export interface FinancialClaim {
  id: string
  claim_type: string
  subject: string
  amount: number | null
  currency: string | null
  verification_status: string
  confidence: number
  confidence_level: string
}

export interface Evidence {
  id: string
  evidence_type: string
  source_name: string
  received_at: string
  status: string
  checksum: string | null
  source_reference: string | null
}

export interface EvidenceLink {
  id: string
  claim_id: string
  evidence_id: string
  verification_status: string
  confidence: number
  explanation: string | null
}

export interface FinancialProof {
  id: string
  subject: string
  status: string
  overall_confidence: number
  evaluation_reasons: string[]
}

export interface FinancialProofAggregate {
  proof: FinancialProof
  claims: FinancialClaim[]
  evidence: Evidence[]
  evidence_links: EvidenceLink[]
}

export interface ProofEvaluation {
  id: string
  proof_id: string
  status: string
  overall_confidence: number
  evaluation_reasons: string[]
  evaluated_at: string
}

export interface FinancialProofCreateRequest {
  id?: string
  subject: string
  claims: FinancialClaimCreateRequest[]
  evidence: EvidenceCreateRequest[]
  evidence_links: EvidenceLinkCreateRequest[]
}

export interface FinancialClaimCreateRequest {
  id?: string
  claim_type: string
  subject: string
  amount?: number | null
  currency?: string | null
  verification_status?: string
  confidence?: number
  confidence_level?: string
}

export interface EvidenceCreateRequest {
  id?: string
  evidence_type: string
  source_name: string
  received_at: string
  status?: string
  checksum?: string | null
  source_reference?: string | null
}

export interface EvidenceLinkCreateRequest {
  id?: string
  claim_id: string
  evidence_id: string
  verification_status?: string
  confidence?: number
  explanation?: string | null
}
