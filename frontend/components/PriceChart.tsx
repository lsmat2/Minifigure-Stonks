/**
 * PriceChart - Price history visualization using Recharts
 * Displays min, max, average, and median prices over time
 */
'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import type { PriceSnapshot } from '@/lib/types';

interface PriceChartProps {
  snapshots: PriceSnapshot[];
  showMin?: boolean;
  showMax?: boolean;
  showAvg?: boolean;
  showMedian?: boolean;
}

export default function PriceChart({
  snapshots,
  showMin = false,
  showMax = false,
  showAvg = true,
  showMedian = true
}: PriceChartProps) {
  // Transform data for chart
  const chartData = snapshots.map(snapshot => ({
    date: new Date(snapshot.date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    }),
    fullDate: snapshot.date,
    min: parseFloat(snapshot.min_price_usd),
    max: parseFloat(snapshot.max_price_usd),
    avg: parseFloat(snapshot.avg_price_usd),
    median: parseFloat(snapshot.median_price_usd),
    listings: snapshot.listing_count
  }));

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg dark:border-gray-700 dark:bg-gray-800">
          <p className="mb-2 font-semibold text-gray-900 dark:text-white">
            {new Date(data.fullDate).toLocaleDateString('en-US', {
              month: 'long',
              day: 'numeric',
              year: 'numeric'
            })}
          </p>
          {showAvg && (
            <p className="text-sm text-blue-600 dark:text-blue-400">
              Average: ${data.avg.toFixed(2)}
            </p>
          )}
          {showMedian && (
            <p className="text-sm text-green-600 dark:text-green-400">
              Median: ${data.median.toFixed(2)}
            </p>
          )}
          {showMin && (
            <p className="text-sm text-orange-600 dark:text-orange-400">
              Min: ${data.min.toFixed(2)}
            </p>
          )}
          {showMax && (
            <p className="text-sm text-red-600 dark:text-red-400">
              Max: ${data.max.toFixed(2)}
            </p>
          )}
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {data.listings} listings
          </p>
        </div>
      );
    }
    return null;
  };

  if (chartData.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-lg border border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800">
        <p className="text-gray-500 dark:text-gray-400">No price history available</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
          <XAxis
            dataKey="date"
            className="text-xs text-gray-600 dark:text-gray-400"
            tick={{ fill: 'currentColor' }}
          />
          <YAxis
            className="text-xs text-gray-600 dark:text-gray-400"
            tick={{ fill: 'currentColor' }}
            tickFormatter={(value) => `$${value}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{
              paddingTop: '20px'
            }}
            iconType="line"
          />

          {showAvg && (
            <Line
              type="monotone"
              dataKey="avg"
              stroke="#2563eb"
              strokeWidth={2}
              name="Average"
              dot={false}
            />
          )}
          {showMedian && (
            <Line
              type="monotone"
              dataKey="median"
              stroke="#16a34a"
              strokeWidth={2}
              name="Median"
              dot={false}
            />
          )}
          {showMin && (
            <Line
              type="monotone"
              dataKey="min"
              stroke="#ea580c"
              strokeWidth={1.5}
              name="Min"
              dot={false}
              strokeDasharray="5 5"
            />
          )}
          {showMax && (
            <Line
              type="monotone"
              dataKey="max"
              stroke="#dc2626"
              strokeWidth={1.5}
              name="Max"
              dot={false}
              strokeDasharray="5 5"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
