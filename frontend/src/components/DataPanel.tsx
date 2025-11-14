import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import type { Filing, DataPanelFilters, SortField, SortDirection, ApiError } from '../types';
import { FilingTable } from './FilingTable';
import { MetricsCard } from './MetricsCard';
import { FilterPanel } from './FilterPanel';
import { ErrorMessage } from './ErrorMessage';
import { LoadingSpinner } from './LoadingSpinner';
import { DataVisualization } from './DataVisualization';

export function DataPanel() {
  const [filings, setFilings] = useState<Filing[]>([]);
  const [filteredFilings, setFilteredFilings] = useState<Filing[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<ApiError | null>(null);
  const [filters, setFilters] = useState<DataPanelFilters>({});
  const [sortField, setSortField] = useState<SortField>('filing_date');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Fetch filings data
  const fetchFilings = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await apiClient.getFilings({
        issuer: filters.issuer,
        asset_class: filters.assetClass,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
      });
      setFilings(data);
      setFilteredFilings(data);
    } catch (err) {
      setError(err as ApiError);
      setFilings([]);
      setFilteredFilings([]);
    } finally {
      setIsLoading(false);
    }
  }, [filters]);

  // Apply client-side filters
  useEffect(() => {
    let filtered = [...filings];

    if (filters.minRiskScore !== undefined) {
      filtered = filtered.filter(f => (f.risk_score ?? 0) >= filters.minRiskScore!);
    }

    if (filters.maxRiskScore !== undefined) {
      filtered = filtered.filter(f => (f.risk_score ?? 0) <= filters.maxRiskScore!);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];

      if (aValue === undefined || bValue === undefined) return 0;

      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }

      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortDirection === 'asc' ? aValue - bValue : bValue - aValue;
      }

      return 0;
    });

    setFilteredFilings(filtered);
  }, [filings, filters.minRiskScore, filters.maxRiskScore, sortField, sortDirection]);

  // Initial load
  useEffect(() => {
    fetchFilings();
  }, [fetchFilings]);

  // Calculate aggregate metrics
  const metrics = {
    totalFilings: filteredFilings.length,
    avgDelinquencyRate: filteredFilings.length > 0
      ? filteredFilings.reduce((sum, f) => sum + f.delinquency_30_days, 0) / filteredFilings.length
      : 0,
    avgDefaultRate: filteredFilings.length > 0
      ? filteredFilings.reduce((sum, f) => sum + f.cumulative_default_rate, 0) / filteredFilings.length
      : 0,
    avgRiskScore: filteredFilings.length > 0
      ? filteredFilings.reduce((sum, f) => sum + (f.risk_score ?? 0), 0) / filteredFilings.length
      : 0,
    totalPoolBalance: filteredFilings.reduce((sum, f) => sum + f.current_pool_balance, 0),
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const handleRefresh = () => {
    fetchFilings();
  };

  return (
    <div className="data-panel">
      <div className="data-panel__header">
        <h1>ABS Analytics Data Panel</h1>
        <button
          className="refresh-button"
          onClick={handleRefresh}
          disabled={isLoading}
        >
          {isLoading ? 'Refreshing...' : 'Refresh Data'}
        </button>
      </div>

      <FilterPanel
        filters={filters}
        onFiltersChange={setFilters}
        onApply={fetchFilings}
      />

      {error && (
        <ErrorMessage
          error={error}
          onRetry={handleRefresh}
        />
      )}

      {isLoading ? (
        <LoadingSpinner />
      ) : (
        <>
          <MetricsCard metrics={metrics} />

          <DataVisualization filings={filteredFilings} />

          <FilingTable
            filings={filteredFilings}
            sortField={sortField}
            sortDirection={sortDirection}
            onSort={handleSort}
          />
        </>
      )}
    </div>
  );
}
