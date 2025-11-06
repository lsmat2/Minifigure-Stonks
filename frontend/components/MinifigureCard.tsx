/**
 * MinifigureCard - Individual minifigure display card
 * Shows thumbnail, name, theme, year, and latest price info
 */
import Link from 'next/link';
import Image from 'next/image';
import type { Minifigure } from '@/lib/types';

interface MinifigureCardProps {
  minifigure: Minifigure;
}

export default function MinifigureCard({ minifigure }: MinifigureCardProps) {
  return (
    <Link href={`/minifigures/${minifigure.id}`}>
      <div className="group cursor-pointer rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-all hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
        {/* Image */}
        <div className="relative mb-3 aspect-square overflow-hidden rounded-md bg-gray-100 dark:bg-gray-700">
          {minifigure.thumbnail_url || minifigure.image_url ? (
            <Image
              src={minifigure.thumbnail_url || minifigure.image_url || ''}
              alt={minifigure.name}
              fill
              className="object-contain p-2 transition-transform group-hover:scale-105"
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
            />
          ) : (
            <div className="flex h-full items-center justify-center text-gray-400">
              <svg
                className="h-16 w-16"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
          )}
        </div>

        {/* Info */}
        <div className="space-y-1">
          <h3 className="line-clamp-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
            {minifigure.name}
          </h3>

          <p className="text-xs font-medium text-gray-500 dark:text-gray-400">
            {minifigure.set_number}
          </p>

          {minifigure.theme && (
            <p className="text-xs text-gray-600 dark:text-gray-300">
              {minifigure.theme}
              {minifigure.subtheme && ` - ${minifigure.subtheme}`}
            </p>
          )}

          {minifigure.year_released && (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {minifigure.year_released}
            </p>
          )}
        </div>
      </div>
    </Link>
  );
}
