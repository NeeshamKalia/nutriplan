import { useState, useEffect } from 'react';
import { Card } from '../../components/ui/Card';
import { dashboardApi, DashboardStats } from '../../api/dashboard';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await dashboardApi.getStats();
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

      <div className="grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 'var(--space-4)' }}>
        <Card>
          <h3 className="text-muted text-sm font-medium mb-1">Active Clients</h3>
          <p className="text-3xl font-bold">{stats?.active_clients || 0}</p>
        </Card>
        <Card>
          <h3 className="text-muted text-sm font-medium mb-1">Plans Generated</h3>
          <p className="text-3xl font-bold">{stats?.plans_generated_this_month || 0}</p>
        </Card>
        <Card>
          <h3 className="text-muted text-sm font-medium mb-1">Pending Approvals</h3>
          <p className={`text-3xl font-bold ${stats?.pending_approvals ? 'text-warning' : ''}`}>
            {stats?.pending_approvals || 0}
          </p>
        </Card>
      </div>
      
      <Card>
        <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
        <p className="text-muted text-center py-8">No recent activity.</p>
      </Card>
    </div>
  );
}
