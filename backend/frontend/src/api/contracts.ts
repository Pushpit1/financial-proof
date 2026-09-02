import { apiClient } from './client'
import type {
  FinancialContract,
  FinancialContractCreateRequest,
  FinancialContractDecision,
  FinancialContractDecisionEvaluateRequest,
} from '../types/contract'

export interface FinancialContractCompileRequest {
  source_text: string
}

export interface FinancialContractCompileResponse {
  source_text: string
  contract: FinancialContract
}

export function createContract(
  request: FinancialContractCreateRequest,
): Promise<FinancialContract> {
  return apiClient.post<FinancialContract>('/contracts', request)
}

export function getContract(
  contractId: string,
): Promise<FinancialContract> {
  return apiClient.get<FinancialContract>(`/contracts/${contractId}`)
}

export function getContractVersion(
  name: string,
  version: number,
): Promise<FinancialContract> {
  return apiClient.get<FinancialContract>(
    `/contracts/${encodeURIComponent(name)}/${version}`,
  )
}

export function compileContract(
  request: FinancialContractCompileRequest,
): Promise<FinancialContractCompileResponse> {
  return apiClient.post<FinancialContractCompileResponse>(
    '/contracts/compile',
    request,
  )
}

export function evaluateContract(
  contractId: string,
  request: FinancialContractDecisionEvaluateRequest,
): Promise<FinancialContractDecision> {
  return apiClient.post<FinancialContractDecision>(
    `/contracts/${contractId}/decisions`,
    request,
  )
}

export function listContractDecisions(
  contractId: string,
  limit = 50,
  offset = 0,
): Promise<FinancialContractDecision[]> {
  return apiClient.get<FinancialContractDecision[]>(
    `/contracts/${contractId}/decisions?limit=${limit}&offset=${offset}`,
  )
}
