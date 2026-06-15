import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { dashboardApi, DashboardOverview } from '../../api/dashboard';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

function formatActivity(type: string) {
  if (type === 'meal_logged') return 'Meal logged';
  if (type === 'plan_delivered') return 'Plan delivered';
  return type.replace(/_/g, ' ');
}

function formatTimestamp(timestamp: string) {
  return new Date(timestamp).toLocaleString('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await dashboardApi.getOverview();
        setStats(data);
      } catch (err) {
        console.error('Failed to load dashboard stats', err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-2">Dashboard</h1>
        <p className="text-muted">Overview of your practice.</p>
      </div>

      <div
        className="grid"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        <Card>
          <h3 className="text-muted text-sm font-medium mb-1">Active Clients</h3>
          <p className="text-3xl font-bold">{stats?.active_clients ?? 0}</p>
          <p className="text-muted text-sm">{stats?.total_clients ?? 0} total</p>
        </Card>
        <Card>
          <h3 className="text-muted text-sm font-medium mb-1">Avg Adherence</h3>
          <p className="text-3xl font-bold">{stats?.avg_adherence_pct ?? 0}%</p>
          <p className="text-muted text-sm">Last 7 days</p>
        </Card>
        <Card>
          <h3 className="text-muted text-sm font-medium mb-1">Plans This Month</h3>
          <p className="text-3xl font-bold">{stats?.plans_this_month ?? 0}</p>
        </Card>
        <Card>
          <h3 className="text-muted text-sm font-medium mb-1">Pending Approvals</h3>
          <p
            className={`text-3xl font-bold ${stats?.pending_approvals ? 'text-warning' : ''}`}
          >
            {stats?.pending_approvals ?? 0}
          </p>
        </Card>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 'var(--space-4)',
        }}
      >
        <Card>
          <h2 className="text-lg font-semibold mb-4">Clients Needing Attention</h2>
          {stats?.clients_needing_attention?.length ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {stats.clients_needing_attention.map((client) => (
                <button
                  key={client.id}
                  onClick={() => navigate(`/clients/${client.id}`)}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.75rem',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    background: 'transparent',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <div>
                    <p className="font-medium">{client.name}</p>
                    {client.last_interaction && (
                      <p className="text-muted text-sm">
                        Last log: {client.last_interaction}
                      </p>
                    )}
                  </div>
                  <span className="text-red-600 font-semibold">{client.adherence_pct}%</span>
                </button>
              ))}
            </div>
          ) : (
            <p className="text-muted text-center py-8">All clients are on track.</p>
          )}
        </Card>

        <Card>
          <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
          {stats?.recent_activity?.length ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {stats.recent_activity.map((item, index) => (
                <div
                  key={`${item.type}-${item.timestamp}-${index}`}
                  style={{
                    padding: '0.75rem',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem' }}>
                    <p className="font-medium">{formatActivity(item.type)}</p>
                    <p className="text-muted text-sm">{formatTimestamp(item.timestamp)}</p>
                  </div>
                  <p className="text-sm" style={{ marginTop: '0.25rem' }}>
                    {item.client}
                    {item.detail ? ` · ${item.detail}` : ''}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted text-center py-8">No recent activity.</p>
          )}
        </Card>
      </div>
    </div>
  );
}
