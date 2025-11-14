import { format } from 'date-fns';
import type { Filing, SortField, SortDirection } from '../types';

interface FilingTableProps {
  filings: Filing[];
  sortField: SortField;
  sortDirection: SortDirection;
  onSort: (field: SortField) => void;
}

export function FilingTable({ filings, sortField, sortDirection, onSort }: FilingTableProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  const formatDate = (dateString: string) => {
    try {
      return format(new Date(dateString), 'MM/dd/yyyy');
    } catch {
      return dateString;
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <span className="sort-icon">⇅</span>;
    }
    return sortDirection === 'asc'
      ? <span className="sort-icon active">↑</span>
      : <span className="sort-icon active">↓</span>;
  };

  if (filings.length === 0) {
    return (
      <div className="no-data">
        <p>No filings found. Try adjusting your filters.</p>
      </div>
    );
  }

  return (
    <div className="filing-table-container">
      <table className="filing-table">
        <thead>
          <tr>
            <th onClick={() => onSort('filing_date')}>
              Filing Date <SortIcon field="filing_date" />
            </th>
            <th onClick={() => onSort('issuer_name')}>
              Issuer <SortIcon field="issuer_name" />
            </th>
            <th onClick={() => onSort('deal_name')}>
              Deal Name <SortIcon field="deal_name" />
            </th>
            <th onClick={() => onSort('asset_class')}>
              Asset Class <SortIcon field="asset_class" />
            </th>
            <th onClick={() => onSort('current_pool_balance')}>
              Pool Balance <SortIcon field="current_pool_balance" />
            </th>
            <th onClick={() => onSort('delinquency_30_days')}>
              Delinquency (30d) <SortIcon field="delinquency_30_days" />
            </th>
            <th onClick={() => onSort('cumulative_default_rate')}>
              Default Rate <SortIcon field="cumulative_default_rate" />
            </th>
            <th onClick={() => onSort('weighted_average_fico')}>
              Avg FICO <SortIcon field="weighted_average_fico" />
            </th>
            <th onClick={() => onSort('risk_score')}>
              Risk Score <SortIcon field="risk_score" />
            </th>
            <th onClick={() => onSort('data_quality_score')}>
              Quality <SortIcon field="data_quality_score" />
            </th>
          </tr>
        </thead>
        <tbody>
          {filings.map((filing) => (
            <tr key={filing.filing_id}>
              <td>{formatDate(filing.filing_date)}</td>
              <td>{filing.issuer_name}</td>
              <td>{filing.deal_name}</td>
              <td>
                <span className="asset-class-badge">{filing.asset_class}</span>
              </td>
              <td className="numeric">{formatCurrency(filing.current_pool_balance)}</td>
              <td className="numeric">{formatPercent(filing.delinquency_30_days)}</td>
              <td className="numeric">{formatPercent(filing.cumulative_default_rate)}</td>
              <td className="numeric">{filing.weighted_average_fico.toFixed(0)}</td>
              <td className="numeric">
                {filing.risk_score !== undefined ? (
                  <span className={`risk-badge risk-${getRiskLevel(filing.risk_score)}`}>
                    {filing.risk_score.toFixed(2)}
                  </span>
                ) : (
                  <span className="no-data">N/A</span>
                )}
              </td>
              <td className="numeric">
                <span className="quality-badge">{filing.data_quality_score.toFixed(0)}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function getRiskLevel(score: number): string {
  if (score < 0.3) return 'low';
  if (score < 0.6) return 'medium';
  if (score < 0.8) return 'high';
  return 'critical';
}
