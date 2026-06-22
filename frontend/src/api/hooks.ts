import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';

export interface Transaction {
  id: string;
  date: string;
  description_raw: string;
  description_clean: string;
  amount: number;
  type: 'credit' | 'debit';
  category: string;
  category_confidence?: number;
  is_recurring: boolean;
  recurring_group_id?: string;
  balance?: number;
  metadata?: any;
}

export interface RecurringGroup {
  id: string;
  label: string;
  category: string;
  frequency: string;
  typical_amount: number;
  last_seen_date?: string;
  transaction_ids: string[];
  confidence?: number;
}

export interface UploadSession {
  id: string;
  filename: string;
  status: 'pending' | 'parsing' | 'processing' | 'ready' | 'failed';
  uploaded_at: string;
  expires_at: string;
  error_message?: string;
}

export interface AnalyticsMetrics {
  total_income: number;
  total_spend: number;
  savings: number;
  savings_rate: number;
  recurring_total?: number;
}

export interface AnalyticsResult {
  metrics: AnalyticsMetrics;
  top_categories: { category: string; amount: number }[];
  biggest_transactions: Transaction[];
}

export interface UploadResponse {
  session_id: string;
  status: string;
  message: string;
}

// 1. Upload Statement Mutation
export function useUploadStatement() {
  return useMutation<UploadResponse, Error, { file: File; bankHint?: string }>({
    mutationFn: async ({ file, bankHint }) => {
      const formData = new FormData();
      formData.append('file', file);
      if (bankHint) {
        formData.append('bank_hint', bankHint);
      }
      return apiClient<UploadResponse>('/upload', {
        method: 'POST',
        body: formData,
      });
    },
  });
}

// 2. Session Status Query
export function useSessionStatus(sessionId: string | null) {
  return useQuery<UploadSession, Error>({
    queryKey: ['session', sessionId],
    queryFn: () => apiClient<UploadSession>(`/sessions/${sessionId}`),
    enabled: !!sessionId,
    refetchInterval: (query) => {
      // Poll if status is pending, parsing, or processing
      const status = query.state.data?.status;
      if (status === 'pending' || status === 'parsing' || status === 'processing') {
        return 1500;
      }
      return false;
    },
  });
}

// 3. Paginated Transactions Query
export function useTransactions(
  sessionId: string | null,
  params: { page?: number; limit?: number; category?: string; is_recurring?: boolean; search?: string } = {}
) {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.limit) queryParams.append('limit', params.limit.toString());
  if (params.category && params.category !== 'all') queryParams.append('category', params.category);
  if (params.is_recurring !== undefined) queryParams.append('is_recurring', params.is_recurring.toString());
  if (params.search) queryParams.append('search', params.search);

  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';

  return useQuery<{ total_count: number; page: number; limit: number; transactions: Transaction[] }, Error>({
    queryKey: ['transactions', sessionId, params],
    queryFn: () => apiClient<{ total_count: number; page: number; limit: number; transactions: Transaction[] }>(
      `/sessions/${sessionId}/transactions${queryString}`
    ),
    enabled: !!sessionId,
  });
}

// 4. Category Override Mutation
export function useOverrideCategory() {
  const queryClient = useQueryClient();
  return useMutation<
    { transaction_id: string; category: string; message: string },
    Error,
    { sessionId: string; transactionId: string; category: string }
  >({
    mutationFn: ({ sessionId, transactionId, category }) =>
      apiClient<{ transaction_id: string; category: string; message: string }>(
        `/sessions/${sessionId}/transactions/${transactionId}?category=${encodeURIComponent(category)}`,
        { method: 'PATCH' }
      ),
    onSuccess: (_, variables) => {
      // Invalidate queries to refresh UI state
      queryClient.invalidateQueries({ queryKey: ['transactions', variables.sessionId] });
      queryClient.invalidateQueries({ queryKey: ['analytics', variables.sessionId] });
    },
  });
}

// 5. Recurring Payments Query
export function useRecurringPayments(sessionId: string | null) {
  return useQuery<RecurringGroup[], Error>({
    queryKey: ['recurring', sessionId],
    queryFn: () => apiClient<RecurringGroup[]>(`/sessions/${sessionId}/recurring`),
    enabled: !!sessionId,
  });
}

// 6. Analytics Query
export function useAnalytics(sessionId: string | null) {
  return useQuery<AnalyticsResult, Error>({
    queryKey: ['analytics', sessionId],
    queryFn: () => apiClient<AnalyticsResult>(`/sessions/${sessionId}/analytics`),
    enabled: !!sessionId,
  });
}

// 7. Spending Insights Query
export function useInsights(sessionId: string | null) {
  return useQuery<string[], Error>({
    queryKey: ['insights', sessionId],
    queryFn: () => apiClient<string[]>(`/sessions/${sessionId}/insights`),
    enabled: !!sessionId,
  });
}

// 8. Delete Session Mutation
export function useDeleteSession() {
  const queryClient = useQueryClient();
  return useMutation<{ message: string }, Error, string>({
    mutationFn: (sessionId) => apiClient<{ message: string }>(`/sessions/${sessionId}`, { method: 'DELETE' }),
    onSuccess: (_, sessionId) => {
      queryClient.invalidateQueries({ queryKey: ['session', sessionId] });
    },
  });
}
