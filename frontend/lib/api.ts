/**
 * API Client for Minifigure-Stonks Backend
 *
 * Type-safe fetch wrapper with error handling
 */

import type {
  Minifigure,
  MinifigureList,
  PriceListing,
  PriceHistory,
  PriceSnapshot,
  ConditionType,
  ApiError
} from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        const error: ApiError = await response.json().catch(() => ({
          detail: `HTTP ${response.status}: ${response.statusText}`,
        }));
        throw new Error(error.detail);
      }

      return response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('An unknown error occurred');
    }
  }

  // Health endpoints
  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.fetch('/health');
  }

  // Minifigure endpoints
  async getMinifigures(params?: {
    page?: number;
    page_size?: number;
    theme?: string;
    year?: number;
    search?: string;
  }): Promise<MinifigureList> {
    const query = new URLSearchParams();
    if (params?.page) query.append('page', params.page.toString());
    if (params?.page_size) query.append('page_size', params.page_size.toString());
    if (params?.theme) query.append('theme', params.theme);
    if (params?.year) query.append('year', params.year.toString());
    if (params?.search) query.append('search', params.search);

    const queryString = query.toString();
    return this.fetch(`/minifigures${queryString ? `?${queryString}` : ''}`);
  }

  async getMinifigure(id: string): Promise<Minifigure> {
    return this.fetch(`/minifigures/${id}`);
  }

  // Price endpoints
  async getMinifigurePrices(
    id: string,
    params?: {
      condition?: ConditionType;
      source_id?: number;
      start_date?: string;
      end_date?: string;
      limit?: number;
    }
  ): Promise<PriceListing[]> {
    const query = new URLSearchParams();
    if (params?.condition) query.append('condition', params.condition);
    if (params?.source_id) query.append('source_id', params.source_id.toString());
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);
    if (params?.limit) query.append('limit', params.limit.toString());

    const queryString = query.toString();
    return this.fetch(`/minifigures/${id}/prices${queryString ? `?${queryString}` : ''}`);
  }

  async getMinifigurePriceHistory(
    id: string,
    params?: {
      start_date?: string;
      end_date?: string;
    }
  ): Promise<PriceHistory> {
    const query = new URLSearchParams();
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);

    const queryString = query.toString();
    return this.fetch(`/minifigures/${id}/price-history${queryString ? `?${queryString}` : ''}`);
  }

  async getPriceSnapshots(params?: {
    minifigure_id?: string;
    date?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
  }): Promise<PriceSnapshot[]> {
    const query = new URLSearchParams();
    if (params?.minifigure_id) query.append('minifigure_id', params.minifigure_id);
    if (params?.date) query.append('date', params.date);
    if (params?.start_date) query.append('start_date', params.start_date);
    if (params?.end_date) query.append('end_date', params.end_date);
    if (params?.page) query.append('page', params.page.toString());
    if (params?.page_size) query.append('page_size', params.page_size.toString());

    const queryString = query.toString();
    return this.fetch(`/snapshots${queryString ? `?${queryString}` : ''}`);
  }
}

// Export singleton instance
export const api = new ApiClient();

// Export class for testing or custom instances
export default ApiClient;
