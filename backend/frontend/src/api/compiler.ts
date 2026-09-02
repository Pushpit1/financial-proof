import { apiClient } from './client'
import type {
  FinancialContractCompileRequest,
  FinancialContractCompileResponse,
} from '../types/compiler'

export function compileContract(
  request: FinancialContractCompileRequest,
): Promise<FinancialContractCompileResponse> {
  return apiClient.post<FinancialContractCompileResponse>(
    '/contracts/compile',
    request,
  )
}
