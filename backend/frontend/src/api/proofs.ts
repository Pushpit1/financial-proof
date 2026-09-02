import { apiClient } from './client'
import type {
  FinancialProofAggregate,
  FinancialProofCreateRequest,
  ProofEvaluation,
} from '../types/proof'

export function listProofs(subject: string): Promise<FinancialProofAggregate['proof'][]> {
  return apiClient.get<FinancialProofAggregate['proof'][]>(
    `/proofs?subject=${encodeURIComponent(subject)}`,
  )
}

export function createProof(
  request: FinancialProofCreateRequest,
): Promise<FinancialProofAggregate> {
  return apiClient.post<FinancialProofAggregate>('/proofs', request)
}

export function getProof(proofId: string): Promise<FinancialProofAggregate> {
  return apiClient.get<FinancialProofAggregate>(`/proofs/${proofId}`)
}

export function evaluateProof(
  proofId: string,
): Promise<FinancialProofAggregate> {
  return apiClient.post<FinancialProofAggregate>(
    `/proofs/${proofId}/evaluate`,
    {},
  )
}

export function listProofEvaluations(
  proofId: string,
): Promise<ProofEvaluation[]> {
  return apiClient.get<ProofEvaluation[]>(
    `/proofs/${proofId}/evaluations`,
  )
}
