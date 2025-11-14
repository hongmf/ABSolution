interface MetricsCardProps {
  metrics: {
    totalFilings: number;
    avgDelinquencyRate: number;
    avgDefaultRate: number;
    avgRiskScore: number;
    totalPoolBalance: number;
  };
}

export function MetricsCard({ metrics }: MetricsCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    return `${(value * 100).toFixed(2)}%`;
  };

  return (
    <div className="metrics-card">
      <div className="metric">
        <div className="metric__label">Total Filings</div>
        <div className="metric__value">{metrics.totalFilings}</div>
      </div>

      <div className="metric">
        <div className="metric__label">Total Pool Balance</div>
        <div className="metric__value">{formatCurrency(metrics.totalPoolBalance)}</div>
      </div>

      <div className="metric">
        <div className="metric__label">Avg Delinquency Rate</div>
        <div className="metric__value">{formatPercent(metrics.avgDelinquencyRate)}</div>
      </div>

      <div className="metric">
        <div className="metric__label">Avg Default Rate</div>
        <div className="metric__value">{formatPercent(metrics.avgDefaultRate)}</div>
      </div>

      <div className="metric">
        <div className="metric__label">Avg Risk Score</div>
        <div className="metric__value risk-score">
          {metrics.avgRiskScore.toFixed(2)}
        </div>
      </div>
    </div>
  );
}
