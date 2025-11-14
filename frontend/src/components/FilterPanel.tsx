import { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import type { DataPanelFilters } from '../types';

interface FilterPanelProps {
  filters: DataPanelFilters;
  onFiltersChange: (filters: DataPanelFilters) => void;
  onApply: () => void;
}

export function FilterPanel({ filters, onFiltersChange, onApply }: FilterPanelProps) {
  const [issuers, setIssuers] = useState<string[]>([]);
  const [assetClasses, setAssetClasses] = useState<string[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // Load filter options
    const loadOptions = async () => {
      try {
        const [issuersList, assetClassesList] = await Promise.all([
          apiClient.getIssuerList(),
          apiClient.getAssetClasses(),
        ]);
        setIssuers(issuersList);
        setAssetClasses(assetClassesList);
      } catch (error) {
        console.error('Error loading filter options:', error);
      }
    };

    loadOptions();
  }, []);

  const handleChange = (key: keyof DataPanelFilters, value: string | number | undefined) => {
    onFiltersChange({
      ...filters,
      [key]: value === '' ? undefined : value,
    });
  };

  const handleClear = () => {
    onFiltersChange({});
  };

  const activeFilterCount = Object.values(filters).filter(v => v !== undefined).length;

  return (
    <div className="filter-panel">
      <div className="filter-panel__header">
        <button
          className="filter-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          Filters {activeFilterCount > 0 && `(${activeFilterCount})`}
          <span className={`toggle-icon ${isExpanded ? 'expanded' : ''}`}>▼</span>
        </button>

        {activeFilterCount > 0 && (
          <button className="clear-filters" onClick={handleClear}>
            Clear All
          </button>
        )}
      </div>

      {isExpanded && (
        <div className="filter-panel__content">
          <div className="filter-group">
            <label htmlFor="issuer-filter">Issuer</label>
            <select
              id="issuer-filter"
              value={filters.issuer || ''}
              onChange={(e) => handleChange('issuer', e.target.value)}
            >
              <option value="">All Issuers</option>
              {issuers.map((issuer) => (
                <option key={issuer} value={issuer}>
                  {issuer}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="asset-class-filter">Asset Class</label>
            <select
              id="asset-class-filter"
              value={filters.assetClass || ''}
              onChange={(e) => handleChange('assetClass', e.target.value)}
            >
              <option value="">All Asset Classes</option>
              {assetClasses.map((assetClass) => (
                <option key={assetClass} value={assetClass}>
                  {assetClass}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="date-from-filter">Date From</label>
            <input
              id="date-from-filter"
              type="date"
              value={filters.dateFrom || ''}
              onChange={(e) => handleChange('dateFrom', e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label htmlFor="date-to-filter">Date To</label>
            <input
              id="date-to-filter"
              type="date"
              value={filters.dateTo || ''}
              onChange={(e) => handleChange('dateTo', e.target.value)}
            />
          </div>

          <div className="filter-group">
            <label htmlFor="min-risk-filter">Min Risk Score</label>
            <input
              id="min-risk-filter"
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={filters.minRiskScore || ''}
              onChange={(e) => handleChange('minRiskScore', e.target.value ? parseFloat(e.target.value) : undefined)}
            />
          </div>

          <div className="filter-group">
            <label htmlFor="max-risk-filter">Max Risk Score</label>
            <input
              id="max-risk-filter"
              type="number"
              min="0"
              max="1"
              step="0.1"
              value={filters.maxRiskScore || ''}
              onChange={(e) => handleChange('maxRiskScore', e.target.value ? parseFloat(e.target.value) : undefined)}
            />
          </div>

          <button className="apply-filters" onClick={onApply}>
            Apply Filters
          </button>
        </div>
      )}
    </div>
  );
}
