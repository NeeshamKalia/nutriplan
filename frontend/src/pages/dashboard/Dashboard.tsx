import { Card } from '../../components/ui/Card';

export function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold mb-2">Dashboard</h1>
        <p className="text-muted">Overview of your practice.</p>
      </div>

      <div className="grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 'var(--space-4)' }}>
        <Card>
          <h3 className="text-muted text-sm font-medium mb-1">Active Clients</h3>
          <p className="text-3xl font-bold">0</p>
        </Card>
        <Card>
          <h3 className="text-muted text-sm font-medium mb-1">Plans Generated (This Month)</h3>
          <p className="text-3xl font-bold">0</p>
        </Card>
        <Card>
          <h3 className="text-muted text-sm font-medium mb-1">Pending Approvals</h3>
          <p className="text-3xl font-bold text-warning">0</p>
        </Card>
      </div>
      
      <Card>
        <h2 className="text-lg font-semibold mb-4">Recent Activity</h2>
        <p className="text-muted text-center py-8">No recent activity.</p>
      </Card>
    </div>
  );
}
