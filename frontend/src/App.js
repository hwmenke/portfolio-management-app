import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
} from 'chart.js';
import { Line, Pie } from 'react-chartjs-2';
import './App.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

const API_BASE_URL = process.env.NODE_ENV === 'production' ? '/api' : 'http://localhost:8000';

function App() {
  const [userId, setUserId] = useState(localStorage.getItem('userId') || '');
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (userId) {
      fetchPortfolioData();
    }
  }, [userId]);

  const fetchPortfolioData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/data?user_id=${userId}`);
      setPortfolioData(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch data. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setLoading(true);
      await axios.post(`${API_BASE_URL}/upload?user_id=${userId}`, formData);
      await fetchPortfolioData();
    } catch (err) {
      setError('Failed to upload file. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleManualEntry = async (event) => {
    event.preventDefault();
    const formData = new FormData(event.target);
    const positions = [
      {
        ticker: formData.get('ticker'),
        shares: parseFloat(formData.get('shares')),
        price: parseFloat(formData.get('price'))
      }
    ];

    try {
      setLoading(true);
      await axios.post(`${API_BASE_URL}/manual-entry?user_id=${userId}`, positions);
      await fetchPortfolioData();
      event.target.reset();
    } catch (err) {
      setError('Failed to add position. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/report?user_id=${userId}`,
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'portfolio_report.pdf');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setError('Failed to download report. Please try again.');
      console.error(err);
    }
  };

  if (!userId) {
    return (
      <div className="login-container">
        <h1>Portfolio Dashboard</h1>
        <input
          type="text"
          placeholder="Enter your username"
          onChange={(e) => {
            const value = e.target.value;
            setUserId(value);
            localStorage.setItem('userId', value);
          }}
        />
      </div>
    );
  }

  return (
    <div className="app-container">
      <header>
        <h1>Portfolio Dashboard</h1>
        <div className="user-info">User: {userId}</div>
      </header>

      {error && <div className="error-message">{error}</div>}

      <div className="dashboard-grid">
        {/* Metric Cards */}
        <div className="metric-cards">
          <div className="metric-card">
            <h3>Portfolio Value</h3>
            <p>${portfolioData?.metrics?.total_value?.toFixed(2) || '0.00'}</p>
          </div>
          <div className="metric-card">
            <h3>Daily P&L</h3>
            <p>${portfolioData?.metrics?.daily_pl?.toFixed(2) || '0.00'}</p>
          </div>
          <div className="metric-card">
            <h3>VaR (95%)</h3>
            <p>${portfolioData?.metrics?.var_95?.toFixed(2) || '0.00'}</p>
          </div>
          <div className="metric-card">
            <h3>Volatility</h3>
            <p>{(portfolioData?.metrics?.volatility * 100)?.toFixed(2) || '0.00'}%</p>
          </div>
          <div className="metric-card">
            <h3>Sharpe Ratio</h3>
            <p>{portfolioData?.metrics?.sharpe_ratio?.toFixed(2) || '0.00'}</p>
          </div>
          <div className="metric-card">
            <h3>Beta</h3>
            <p>{portfolioData?.metrics?.beta?.toFixed(2) || '1.00'}</p>
          </div>
        </div>

        {/* Charts */}
        <div className="charts-container">
          {portfolioData && (
            <>
              <div className="chart">
                <Line
                  data={{
                    labels: portfolioData.portfolio.historical_dates,
                    datasets: [
                      {
                        label: 'Portfolio Value',
                        data: portfolioData.portfolio.historical_values,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                      },
                      {
                        label: 'Daily P&L',
                        data: portfolioData.portfolio.historical_pl,
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1
                      }
                    ]
                  }}
                  options={{
                    responsive: true,
                    interaction: {
                      mode: 'index',
                      intersect: false,
                    },
                    scales: {
                      y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                      },
                      y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                          drawOnChartArea: false,
                        },
                      },
                    }
                  }}
                />
              </div>
              <div className="chart">
                <Pie
                  data={{
                    labels: portfolioData.portfolio.positions.map(p => p.ticker),
                    datasets: [{
                      data: portfolioData.portfolio.positions.map(p => p.weight * 100),
                      backgroundColor: [
                        'rgb(255, 99, 132)',
                        'rgb(54, 162, 235)',
                        'rgb(255, 206, 86)',
                        'rgb(75, 192, 192)',
                        'rgb(153, 102, 255)',
                        'rgb(255, 159, 64)'
                      ]
                    }]
                  }}
                  options={{
                    responsive: true,
                    plugins: {
                      legend: {
                        position: 'right',
                      },
                      title: {
                        display: true,
                        text: 'Portfolio Allocation'
                      }
                    }
                  }}
                />
              </div>
            </>
          )}
        </div>

        {/* Position Table */}
        <div className="positions-table">
          <h2>Positions</h2>
          <table>
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Shares</th>
                <th>Market Value</th>
                <th>Unrealized P&L</th>
                <th>Weight %</th>
              </tr>
            </thead>
            <tbody>
              {portfolioData?.portfolio?.positions.map((position, index) => (
                <tr key={index}>
                  <td>{position.ticker}</td>
                  <td>{position.shares}</td>
                  <td>${position.market_value?.toFixed(2)}</td>
                  <td>${position.unrealized_pl?.toFixed(2)}</td>
                  <td>{(position.weight * 100)?.toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Input Forms */}
        <div className="input-forms">
          <div className="upload-form">
            <h3>Upload Excel File</h3>
            <input
              type="file"
              accept=".xlsx"
              onChange={handleFileUpload}
              disabled={loading}
            />
          </div>

          <div className="manual-entry-form">
            <h3>Manual Entry</h3>
            <form onSubmit={handleManualEntry}>
              <input type="text" name="ticker" placeholder="Ticker" required />
              <input type="number" name="shares" placeholder="Shares" required />
              <input type="number" name="price" placeholder="Purchase Price" required />
              <button type="submit" disabled={loading}>Add Position</button>
            </form>
          </div>

          <div className="actions">
            <button onClick={fetchPortfolioData} disabled={loading}>
              Refresh Data
            </button>
            <button onClick={handleDownloadReport} disabled={loading}>
              Download Report
            </button>
          </div>
        </div>
      </div>

      {loading && <div className="loading-overlay">Loading...</div>}
    </div>
  );
}

export default App;
