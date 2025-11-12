import { useMemo } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { format, parseISO } from 'date-fns';
import type { Filing } from '../types';

interface DataVisualizationProps {
  filings: Filing[];
}

export function DataVisualization({ filings }: DataVisualizationProps) {
  // Prepare data for delinquency trends chart
  const delinquencyTrends = useMemo(() => {
    const sortedFilings = [...filings].sort(
      (a, b) => new Date(a.filing_date).getTime() - new Date(b.filing_date).getTime()
    );

    return sortedFilings.slice(-20).map((filing) => ({
      date: format(parseISO(filing.filing_date), 'MM/dd'),
      '30 Days': filing.delinquency_30_days * 100,
      '60 Days': filing.delinquency_60_days * 100,
      '90+ Days': filing.delinquency_90_plus_days * 100,
    }));
  }, [filings]);

  // Prepare data for risk distribution
  const riskDistribution = useMemo(() => {
    const buckets = {
      'Low (0-0.3)': 0,
      'Medium (0.3-0.6)': 0,
      'High (0.6-0.8)': 0,
      'Critical (0.8-1.0)': 0,
    };

    filings.forEach((filing) => {
      const score = filing.risk_score ?? 0;
      if (score < 0.3) buckets['Low (0-0.3)']++;
      else if (score < 0.6) buckets['Medium (0.3-0.6)']++;
      else if (score < 0.8) buckets['High (0.6-0.8)']++;
      else buckets['Critical (0.8-1.0)']++;
    });

    return Object.entries(buckets).map(([name, count]) => ({ name, count }));
  }, [filings]);

  // Prepare data for asset class breakdown
  const assetClassBreakdown = useMemo(() => {
    const breakdown = new Map<string, number>();

    filings.forEach((filing) => {
      const current = breakdown.get(filing.asset_class) || 0;
      breakdown.set(filing.asset_class, current + filing.current_pool_balance);
    });

    return Array.from(breakdown.entries())
      .map(([name, balance]) => ({
        name,
        balance: balance / 1_000_000, // Convert to millions
      }))
      .sort((a, b) => b.balance - a.balance);
  }, [filings]);

  // Prepare data for FICO score trends
  const ficoTrends = useMemo(() => {
    const sortedFilings = [...filings].sort(
      (a, b) => new Date(a.filing_date).getTime() - new Date(b.filing_date).getTime()
    );

    return sortedFilings.slice(-20).map((filing) => ({
      date: format(parseISO(filing.filing_date), 'MM/dd'),
      fico: filing.weighted_average_fico,
      ltv: filing.weighted_average_ltv * 100,
    }));
  }, [filings]);

  if (filings.length === 0) {
    return null;
  }

  return (
    <div className="data-visualization">
      <h2 className="visualization-title">Analytics Dashboard</h2>

      <div className="charts-grid">
        <div className="chart-container">
          <h3>Delinquency Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={delinquencyTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis label={{ value: 'Rate (%)', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value: number) => `${value.toFixed(2)}%`} />
              <Legend />
              <Line type="monotone" dataKey="30 Days" stroke="#17a2b8" strokeWidth={2} />
              <Line type="monotone" dataKey="60 Days" stroke="#ffc107" strokeWidth={2} />
              <Line type="monotone" dataKey="90+ Days" stroke="#dc3545" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Risk Score Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={riskDistribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Bar dataKey="count" fill="#0066cc" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Pool Balance by Asset Class ($ Millions)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={assetClassBreakdown}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis label={{ value: 'Balance ($M)', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value: number) => `$${value.toFixed(2)}M`} />
              <Bar dataKey="balance" fill="#28a745" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-container">
          <h3>Credit Quality Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={ficoTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis
                yAxisId="left"
                label={{ value: 'FICO Score', angle: -90, position: 'insideLeft' }}
              />
              <YAxis
                yAxisId="right"
                orientation="right"
                label={{ value: 'LTV (%)', angle: 90, position: 'insideRight' }}
              />
              <Tooltip />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="fico"
                stroke="#0066cc"
                strokeWidth={2}
                name="Avg FICO"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="ltv"
                stroke="#ff6b35"
                strokeWidth={2}
                name="Avg LTV"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
