/**
 * Minifigure Detail Page
 * Displays minifigure information and price history
 */
'use client';

import { useState } from 'react';
import { use } from 'react';
import useSWR from 'swr';
import Link from 'next/link';
import Image from 'next/image';
import { api } from '@/lib/api';
import PriceChart from '@/components/PriceChart';
import PriceStats from '@/components/PriceStats';
import type { Minifigure, PriceHistory } from '@/lib/types';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function MinifigureDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const [timeRange, setTimeRange] = useState('30'); // days

  // Fetch minifigure details
  const { data: minifigure, error: minifigError } = useSWR<Minifigure>(
    `minifigure-${id}`,
    () => api.getMinifigure(id)
  );

  // Fetch price history
  const { data: priceHistory, error: priceError } = useSWR<PriceHistory>(
    ['price-history', id, timeRange],
    () => {
      const endDate = new Date();
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - parseInt(timeRange));

      return api.getMinifigurePriceHistory(id, {
        start_date: startDate.toISOString().split('T')[0],
        end_date: endDate.toISOString().split('T')[0]
      });
    }
  );

  const isLoading = !minifigure && !minifigError;
  const latestSnapshot = priceHistory?.snapshots[priceHistory.snapshots.length - 1];

  if (minifigError) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-900 dark:bg-red-900/20">
            <h2 className="mb-2 text-lg font-semibold text-red-900 dark:text-red-200">
              Error Loading Minifigure
            </h2>
            <p className="text-red-700 dark:text-red-300">{minifigError.message}</p>
            <Link
              href="/minifigures"
              className="mt-4 inline-block text-red-800 underline dark:text-red-200"
            >
              Back to Browse
            </Link>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <nav className="mb-6 text-sm">
          <Link href="/" className="text-blue-600 hover:underline dark:text-blue-400">
            Home
          </Link>
          <span className="mx-2 text-gray-500">/</span>
          <Link href="/minifigures" className="text-blue-600 hover:underline dark:text-blue-400">
            Browse
          </Link>
          <span className="mx-2 text-gray-500">/</span>
          <span className="text-gray-900 dark:text-white">{minifigure?.name}</span>
        </nav>

        {/* Minifigure Header */}
        <div className="mb-8 grid gap-8 lg:grid-cols-3">
          {/* Image */}
          <div className="lg:col-span-1">
            <div className="relative aspect-square overflow-hidden rounded-lg bg-white dark:bg-gray-800">
              {minifigure?.image_url ? (
                <Image
                  src={minifigure.image_url}
                  alt={minifigure.name}
                  fill
                  className="object-contain p-8"
                  priority
                />
              ) : (
                <div className="flex h-full items-center justify-center text-gray-400">
                  <svg className="h-32 w-32" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1}
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                </div>
              )}
            </div>
          </div>

          {/* Info */}
          <div className="lg:col-span-2">
            <h1 className="mb-2 text-3xl font-bold text-gray-900 dark:text-white">
              {minifigure?.name}
            </h1>

            <div className="mb-6 space-y-2 text-gray-600 dark:text-gray-400">
              <p>
                <span className="font-medium">Set Number:</span> {minifigure?.set_number}
              </p>
              {minifigure?.theme && (
                <p>
                  <span className="font-medium">Theme:</span> {minifigure.theme}
                  {minifigure.subtheme && ` - ${minifigure.subtheme}`}
                </p>
              )}
              {minifigure?.year_released && (
                <p>
                  <span className="font-medium">Year Released:</span> {minifigure.year_released}
                </p>
              )}
              {minifigure?.lego_item_number && (
                <p>
                  <span className="font-medium">LEGO Item Number:</span> {minifigure.lego_item_number}
                </p>
              )}
              {minifigure?.piece_count && (
                <p>
                  <span className="font-medium">Pieces:</span> {minifigure.piece_count}
                </p>
              )}
            </div>

            {/* Current Price Stats */}
            <PriceStats latestSnapshot={latestSnapshot} />
          </div>
        </div>

        {/* Price History Section */}
        <div className="mb-8">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Price History
            </h2>

            {/* Time Range Selector */}
            <div className="flex gap-2">
              {[
                { label: '7D', value: '7' },
                { label: '30D', value: '30' },
                { label: '90D', value: '90' },
                { label: '1Y', value: '365' }
              ].map((range) => (
                <button
                  key={range.value}
                  onClick={() => setTimeRange(range.value)}
                  className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                    timeRange === range.value
                      ? 'bg-blue-600 text-white'
                      : 'border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>

          {/* Chart */}
          <div className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-700 dark:bg-gray-800">
            {priceError ? (
              <div className="flex h-64 items-center justify-center">
                <p className="text-red-600 dark:text-red-400">
                  Error loading price history: {priceError.message}
                </p>
              </div>
            ) : !priceHistory ? (
              <div className="flex h-64 items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600"></div>
              </div>
            ) : (
              <PriceChart
                snapshots={priceHistory.snapshots}
                showAvg={true}
                showMedian={true}
                showMin={false}
                showMax={false}
              />
            )}
          </div>

          {priceHistory && priceHistory.snapshots.length > 0 && (
            <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
              Showing {priceHistory.snapshots.length} days of price data
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
