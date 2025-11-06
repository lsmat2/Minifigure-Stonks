/**
 * TypeScript types matching backend API schemas
 */

export interface Minifigure {
  id: string;
  set_number: string;
  name: string;
  theme: string | null;
  subtheme: string | null;
  year_released: number | null;
  lego_item_number: string | null;
  image_url: string | null;
  thumbnail_url: string | null;
  weight_grams: number | null;
  piece_count: number | null;
  extra_data: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface MinifigureList {
  items: Minifigure[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export type ConditionType = 'NEW' | 'USED' | 'SEALED';

export interface PriceListing {
  id: number;
  minifigure_id: string;
  source_id: number;
  timestamp: string;
  price_usd: string;
  original_price: string | null;
  original_currency: string | null;
  condition: ConditionType;
  quantity_available: number | null;
  seller_name: string | null;
  seller_rating: string | null;
  confidence_score: string | null;
}

export interface PriceSnapshot {
  id: number;
  minifigure_id: string;
  date: string;
  min_price_usd: string;
  max_price_usd: string;
  avg_price_usd: string;
  median_price_usd: string;
  listing_count: number;
  sources_count: number;
  extra_data: Record<string, any>;
}

export interface PriceHistory {
  minifigure_id: string;
  minifigure_name: string;
  set_number: string;
  snapshots: PriceSnapshot[];
}

export interface ApiError {
  detail: string;
}
