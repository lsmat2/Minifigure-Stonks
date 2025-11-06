/**
 * PriceStats - Display current price statistics
 */
import type { PriceSnapshot } from '@/lib/types';

interface PriceStatsProps {
  latestSnapshot?: PriceSnapshot;
}

export default function PriceStats({ latestSnapshot }: PriceStatsProps) {
  if (!latestSnapshot) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-6 dark:border-gray-700 dark:bg-gray-800">
        <p className="text-center text-gray-500 dark:text-gray-400">
          No price data available
        </p>
      </div>
    );
  }

  const stats = [
    {
      label: 'Average Price',
      value: `$${parseFloat(latestSnapshot.avg_price_usd).toFixed(2)}`,
      color: 'text-blue-600 dark:text-blue-400'
    },
    {
      label: 'Median Price',
      value: `$${parseFloat(latestSnapshot.median_price_usd).toFixed(2)}`,
      color: 'text-green-600 dark:text-green-400'
    },
    {
      label: 'Min Price',
      value: `$${parseFloat(latestSnapshot.min_price_usd).toFixed(2)}`,
      color: 'text-orange-600 dark:text-orange-400'
    },
    {
      label: 'Max Price',
      value: `$${parseFloat(latestSnapshot.max_price_usd).toFixed(2)}`,
      color: 'text-red-600 dark:text-red-400'
    }
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
        >
          <p className="mb-1 text-xs text-gray-500 dark:text-gray-400">
            {stat.label}
          </p>
          <p className={`text-2xl font-bold ${stat.color}`}>
            {stat.value}
          </p>
        </div>
      ))}

      <div className="col-span-2 rounded-lg border border-gray-200 bg-white p-4 sm:col-span-4 dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            {latestSnapshot.listing_count} active listings from {latestSnapshot.sources_count} sources
          </span>
          <span className="text-gray-500 dark:text-gray-500">
            Updated: {new Date(latestSnapshot.date).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
}
