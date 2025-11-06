/**
 * Homepage - Landing page for Minifigure-Stonks
 */
import Link from 'next/link';

export default function Home() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-blue-50 to-white dark:from-gray-900 dark:to-gray-800">
      <main className="mx-auto max-w-4xl px-4 py-16 text-center">
        {/* Hero Section */}
        <div className="mb-12">
          <h1 className="mb-4 text-5xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-6xl">
            Minifigure Stonks
          </h1>
          <p className="mb-2 text-xl text-blue-600 dark:text-blue-400">
            Track LEGO Minifigure Prices
          </p>
          <p className="mx-auto max-w-2xl text-lg text-gray-600 dark:text-gray-400">
            Monitor real-time pricing and historical trends for LEGO minifigures across multiple marketplaces.
          </p>
        </div>

        {/* Features Grid */}
        <div className="mb-12 grid gap-6 sm:grid-cols-3">
          <div className="rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
            <div className="mb-3 flex justify-center">
              <svg className="h-12 w-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
              Price History
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              View detailed price trends and historical data for every minifigure
            </p>
          </div>

          <div className="rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
            <div className="mb-3 flex justify-center">
              <svg className="h-12 w-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
              Smart Search
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Filter by theme, year, and search across thousands of minifigures
            </p>
          </div>

          <div className="rounded-lg bg-white p-6 shadow-sm dark:bg-gray-800">
            <div className="mb-3 flex justify-center">
              <svg className="h-12 w-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
              Market Insights
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Track min, max, average, and median prices across sources
            </p>
          </div>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
          <Link
            href="/minifigures"
            className="rounded-lg bg-blue-600 px-8 py-3 text-lg font-medium text-white transition-colors hover:bg-blue-700"
          >
            Browse Minifigures
          </Link>
          <Link
            href="/minifigures"
            className="rounded-lg border border-gray-300 bg-white px-8 py-3 text-lg font-medium text-gray-700 transition-colors hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            View Price Trends
          </Link>
        </div>

        {/* Footer Note */}
        <p className="mt-12 text-sm text-gray-500 dark:text-gray-500">
          Data sourced from BrickLink, eBay, LEGO.com, and Brickset
        </p>
      </main>
    </div>
  );
}
