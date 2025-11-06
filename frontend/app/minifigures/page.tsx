/**
 * Minifigures Browse Page
 * Displays paginated list with search and filters
 */
'use client';

import { useState, useCallback } from 'react';
import useSWR from 'swr';
import { api } from '@/lib/api';
import MinifigureCard from '@/components/MinifigureCard';
import SearchBar from '@/components/SearchBar';
import Filters from '@/components/Filters';
import Pagination from '@/components/Pagination';
import type { MinifigureList } from '@/lib/types';

const PAGE_SIZE = 24;

export default function MinifiguresPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [theme, setTheme] = useState('');
  const [year, setYear] = useState('');

  // Fetch minifigures with current filters
  const { data, error, isLoading } = useSWR<MinifigureList>(
    ['minifigures', page, search, theme, year],
    () => api.getMinifigures({
      page,
      page_size: PAGE_SIZE,
      search: search || undefined,
      theme: theme || undefined,
      year: year ? parseInt(year) : undefined,
    })
  );

  // Fetch all minifigures to extract unique themes and years for filters
  const { data: allMinifigs } = useSWR<MinifigureList>(
    'minifigures-all',
    () => api.getMinifigures({ page_size: 1000 })
  );

  // Extract unique themes and years
  const themes = allMinifigs
    ? Array.from(new Set(allMinifigs.items.map(m => m.theme).filter(Boolean) as string[]))
    : [];

  const years = allMinifigs
    ? Array.from(new Set(allMinifigs.items.map(m => m.year_released).filter(Boolean) as number[]))
    : [];

  // Reset to page 1 when filters change
  const handleSearchChange = useCallback((query: string) => {
    setSearch(query);
    setPage(1);
  }, []);

  const handleThemeChange = useCallback((newTheme: string) => {
    setTheme(newTheme);
    setPage(1);
  }, []);

  const handleYearChange = useCallback((newYear: string) => {
    setYear(newYear);
    setPage(1);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Browse Minifigures
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            {data ? `${data.total} minifigures available` : 'Loading...'}
          </p>
        </div>

        {/* Search and Filters */}
        <div className="mb-6 space-y-4">
          <SearchBar
            onSearch={handleSearchChange}
            initialValue={search}
          />
          <Filters
            selectedTheme={theme}
            selectedYear={year}
            onThemeChange={handleThemeChange}
            onYearChange={handleYearChange}
            themes={themes}
            years={years}
          />
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600"></div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800 dark:border-red-900 dark:bg-red-900/20 dark:text-red-200">
            <p className="font-medium">Error loading minifigures</p>
            <p className="text-sm">{error.message}</p>
          </div>
        )}

        {/* Results Grid */}
        {data && !isLoading && (
          <>
            {data.items.length === 0 ? (
              <div className="py-12 text-center">
                <p className="text-lg text-gray-600 dark:text-gray-400">
                  No minifigures found matching your filters.
                </p>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-500">
                  Try adjusting your search or filters.
                </p>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
                  {data.items.map((minifigure) => (
                    <MinifigureCard key={minifigure.id} minifigure={minifigure} />
                  ))}
                </div>

                {/* Pagination */}
                <div className="mt-8">
                  <Pagination
                    currentPage={page}
                    totalPages={data.pages}
                    onPageChange={setPage}
                  />
                </div>
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}
