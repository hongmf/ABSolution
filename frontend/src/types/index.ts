// Core data types for ABSolution platform

export interface Filing {
  filing_id: string;
  accession_number: string;
  cik: string;
  company_name: string;
  form_type: string;
  filing_date: string;
  fiscal_year: number;
  fiscal_period: string;
  asset_class: string;
  deal_name: string;
  issuer_name: string;
  original_pool_balance: number;
  current_pool_balance: number;
  total_principal_received: number;
  delinquency_30_days: number;
  delinquency_60_days: number;
  delinquency_90_plus_days: number;
  cumulative_default_rate: number;
  cumulative_loss_rate: number;
  weighted_average_fico: number;
  weighted_average_ltv: number;
  weighted_average_dti: number;
  data_quality_score: number;
  risk_score?: number;
}

export interface BenchmarkData {
  issuer_name: string;
  lookback_days: number;
  metrics: {
    avg_delinquency_rate: number;
    avg_default_rate: number;
    avg_loss_rate: number;
    avg_pool_balance: number;
    avg_fico_score: number;
    filing_count: number;
  };
  calculated_at: string;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}

export interface DataPanelFilters {
  issuer?: string;
  assetClass?: string;
  dateFrom?: string;
  dateTo?: string;
  minRiskScore?: number;
  maxRiskScore?: number;
}

export type SortDirection = 'asc' | 'desc';
export type SortField = keyof Filing;
