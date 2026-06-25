'use client';

import { useMemo, useState, type ReactNode } from 'react';
import { Search } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { EmptyState, LoadingState } from '@/components/ui/loading-state';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { cn } from '@/lib/utils';

export type DataTableColumn<T> = {
  id: string;
  header: ReactNode;
  accessor?: keyof T | ((row: T) => ReactNode);
  cell?: (row: T) => ReactNode;
  searchable?: boolean;
  className?: string;
  headerClassName?: string;
};

type DataTableProps<T> = {
  data: T[];
  columns: DataTableColumn<T>[];
  getRowId: (row: T) => string;
  loading?: boolean;
  searchPlaceholder?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  pageSize?: number;
  className?: string;
};

function toSearchText(value: ReactNode): string {
  if (value === null || value === undefined || typeof value === 'boolean') return '';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'bigint') {
    return String(value);
  }
  return '';
}

export function DataTable<T>({
  data,
  columns,
  getRowId,
  loading = false,
  searchPlaceholder = 'Search rows...',
  emptyTitle = 'No rows found',
  emptyDescription,
  pageSize = 20,
  className,
}: DataTableProps<T>) {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  const searchableColumns = useMemo(
    () => columns.filter((column) => column.searchable !== false),
    [columns]
  );

  const filteredData = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return data;

    return data.filter((row) =>
      searchableColumns.some((column) => {
        if (column.cell && !column.accessor) return false;
        const value =
          typeof column.accessor === 'function'
            ? column.accessor(row)
            : column.accessor
              ? row[column.accessor]
              : undefined;

        return toSearchText(value as ReactNode).toLowerCase().includes(query);
      })
    );
  }, [data, search, searchableColumns]);

  const totalPages = Math.max(1, Math.ceil(filteredData.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const startIndex = (currentPage - 1) * pageSize;
  const visibleData = filteredData.slice(startIndex, startIndex + pageSize);

  const renderCell = (row: T, column: DataTableColumn<T>) => {
    if (column.cell) return column.cell(row);
    if (typeof column.accessor === 'function') return column.accessor(row);
    if (column.accessor) return toSearchText(row[column.accessor] as ReactNode) || '—';
    return '—';
  };

  return (
    <section className={cn('rounded-lg border border-border bg-card', className)}>
      <div className="flex flex-col gap-3 border-b border-border p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative w-full sm:max-w-sm">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            placeholder={searchPlaceholder}
            className="pl-9"
            aria-label={searchPlaceholder}
          />
        </div>
        <p className="text-sm text-muted-foreground">
          {filteredData.length} {filteredData.length === 1 ? 'row' : 'rows'}
        </p>
      </div>

      {loading ? (
        <LoadingState
          title="Loading rows"
          description="Please wait while the table data loads."
          className="m-4"
        />
      ) : visibleData.length === 0 ? (
        <EmptyState
          title={search ? 'No matching rows' : emptyTitle}
          description={search ? 'Try a different search term.' : emptyDescription}
          className="m-4"
        />
      ) : (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                {columns.map((column) => (
                  <TableHead key={column.id} className={column.headerClassName}>
                    {column.header}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {visibleData.map((row) => (
                <TableRow key={getRowId(row)}>
                  {columns.map((column) => (
                    <TableCell key={column.id} className={column.className}>
                      {renderCell(row, column)}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>

          {filteredData.length > pageSize ? (
            <div className="flex items-center justify-between border-t border-border p-4">
              <p className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={currentPage <= 1}
                  onClick={() => setPage((value) => Math.max(1, value - 1))}
                >
                  Previous
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={currentPage >= totalPages}
                  onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
                >
                  Next
                </Button>
              </div>
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}
