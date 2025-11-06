/**
 * Filters - Theme and year filter controls
 */
'use client';

interface FiltersProps {
  selectedTheme: string;
  selectedYear: string;
  onThemeChange: (theme: string) => void;
  onYearChange: (year: string) => void;
  themes?: string[];
  years?: number[];
}

export default function Filters({
  selectedTheme,
  selectedYear,
  onThemeChange,
  onYearChange,
  themes = [],
  years = []
}: FiltersProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row">
      {/* Theme Filter */}
      <div className="flex-1">
        <label htmlFor="theme" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Theme
        </label>
        <select
          id="theme"
          value={selectedTheme}
          onChange={(e) => onThemeChange(e.target.value)}
          className="block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
        >
          <option value="">All Themes</option>
          {themes.map((theme) => (
            <option key={theme} value={theme}>
              {theme}
            </option>
          ))}
        </select>
      </div>

      {/* Year Filter */}
      <div className="flex-1">
        <label htmlFor="year" className="mb-1 block text-sm font-medium text-gray-700 dark:text-gray-300">
          Year
        </label>
        <select
          id="year"
          value={selectedYear}
          onChange={(e) => onYearChange(e.target.value)}
          className="block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-white"
        >
          <option value="">All Years</option>
          {years.sort((a, b) => b - a).map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>
      </div>

      {/* Clear Filters */}
      {(selectedTheme || selectedYear) && (
        <div className="flex items-end">
          <button
            onClick={() => {
              onThemeChange('');
              onYearChange('');
            }}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
          >
            Clear Filters
          </button>
        </div>
      )}
    </div>
  );
}
