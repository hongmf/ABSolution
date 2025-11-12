import axios, { AxiosError, AxiosInstance } from 'axios';
import type { Filing, BenchmarkData, ApiError } from '../types';

class ApiClient {
  private client: AxiosInstance;

  constructor(baseURL: string = '/api') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        const apiError: ApiError = {
          message: error.response?.data?.message || error.message || 'An unexpected error occurred',
          code: error.code,
          details: error.response?.data?.details,
        };
        return Promise.reject(apiError);
      }
    );
  }

  async getFilings(params?: {
    issuer?: string;
    asset_class?: string;
    date_from?: string;
    date_to?: string;
    limit?: number;
    offset?: number;
  }): Promise<Filing[]> {
    try {
      const response = await this.client.get<Filing[]>('/filings', { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching filings:', error);
      throw error;
    }
  }

  async getBenchmark(issuerName: string, lookbackDays: number = 90): Promise<BenchmarkData> {
    try {
      const response = await this.client.get<BenchmarkData>('/benchmark', {
        params: { issuer_name: issuerName, lookback_days: lookbackDays },
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching benchmark:', error);
      throw error;
    }
  }

  async getIssuerList(): Promise<string[]> {
    try {
      const response = await this.client.get<string[]>('/issuers');
      return response.data;
    } catch (error) {
      console.error('Error fetching issuers:', error);
      throw error;
    }
  }

  async getAssetClasses(): Promise<string[]> {
    try {
      const response = await this.client.get<string[]>('/asset-classes');
      return response.data;
    } catch (error) {
      console.error('Error fetching asset classes:', error);
      throw error;
    }
  }
}

export const apiClient = new ApiClient();
export default apiClient;
