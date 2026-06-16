import { useState, useEffect } from 'react';
import { adherenceApi, type ClientAdherence } from '../../api/adherence';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { LoadingSpinner } from '../ui/LoadingSpinner';

function statusVariant(status: string): 'success' | 'warning' | 'danger' | 'default' {
  if (status === 'completed') return 'success';
  if (status === 'skipped') return 'warning';
  if (status === 'deviated') return 'danger';
  return 'default';
}

function formatMealType(mealType: string) {
  return mealType.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

export function AdherenceTab({ clientId }: { clientId: string }) {
  const [data, setData] = useState<ClientAdherence | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchAdherence = async () => {
      try {
        const result = await adherenceApi.getClientAdherence(clientId);
        setData(result);
      } catch (err) {
        console.error('Failed to load adherence', err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchAdherence();
  }, [clientId]);

  if (isLoading) return <LoadingSpinner />;

  if (!data) {
    return (
      <Card>
        <p className="text-muted text-center py-8">Could not load adherence data.</p>
      </Card>
    );
  }

  const hasLogs =
    data.total_completed + data.total_skipped + data.total_deviated > 0;

  return (
    <div className="space-y-6">
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '1rem',
        }}
      >
        <Card>
          <p className="text-muted text-sm mb-1">Adherence (7 days)</p>
          <p className="text-3xl font-bold">{data.adherence_pct}%</p>
        </Card>
        <Card>
          <p className="text-muted text-sm mb-1">Completed</p>
          <p className="text-3xl font-bold text-green-600">{data.total_completed}</p>
        </Card>
        <Card>
          <p className="text-muted text-sm mb-1">Skipped</p>
          <p className="text-3xl font-bold text-amber-600">{data.total_skipped}</p>
        </Card>
        <Card>
          <p className="text-muted text-sm mb-1">Deviated</p>
          <p className="text-3xl font-bold text-red-600">{data.total_deviated}</p>
        </Card>
      </div>

      {!hasLogs ? (
        <Card>
          <p className="text-muted text-center py-8">
            No meal logs yet. Client can track meals via WhatsApp with DONE or by reporting deviations.
          </p>
        </Card>
      ) : (
        <>
          <Card>
            <h3 className="font-semibold mb-4">Daily Breakdown</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', textAlign: 'left' }}>
                    <th style={{ padding: '0.75rem' }}>Date</th>
                    <th style={{ padding: '0.75rem' }}>Completed</th>
                    <th style={{ padding: '0.75rem' }}>Skipped</th>
                    <th style={{ padding: '0.75rem' }}>Deviated</th>
                    <th style={{ padding: '0.75rem' }}>Adherence</th>
                  </tr>
                </thead>
                <tbody>
                  {[...data.daily].reverse().map((day) => (
                    <tr key={day.date} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '0.75rem' }}>{day.date}</td>
                      <td style={{ padding: '0.75rem' }}>{day.completed}</td>
                      <td style={{ padding: '0.75rem' }}>{day.skipped}</td>
                      <td style={{ padding: '0.75rem' }}>{day.deviated}</td>
                      <td style={{ padding: '0.75rem' }}>{day.adherence_pct}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {data.by_meal_type.length > 0 && (
            <Card>
              <h3 className="font-semibold mb-4">By Meal Type</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {data.by_meal_type.map((meal) => (
                  <div
                    key={meal.meal_type}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.75rem',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                    }}
                  >
                    <span className="font-medium">{formatMealType(meal.meal_type)}</span>
                    <div style={{ display: 'flex', gap: '1rem', fontSize: '0.875rem' }}>
                      <span className="text-green-600">{meal.completed} done</span>
                      <span className="text-amber-600">{meal.skipped} skipped</span>
                      <span className="text-red-600">{meal.deviated} deviated</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {data.recent_logs.length > 0 && (
            <Card>
              <h3 className="font-semibold mb-4">Recent Logs</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {data.recent_logs.map((log, index) => (
                  <div
                    key={`${log.log_date}-${log.meal_type}-${index}`}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      gap: '1rem',
                      padding: '0.75rem',
                      border: '1px solid var(--border-color)',
                      borderRadius: '8px',
                    }}
                  >
                    <div>
                      <p className="font-medium">
                        {formatMealType(log.meal_type)} · {log.log_date}
                      </p>
                      {log.deviation_note && (
                        <p className="text-muted text-sm" style={{ marginTop: '0.25rem' }}>
                          {log.deviation_note}
                        </p>
                      )}
                    </div>
                    <Badge variant={statusVariant(log.status)}>{log.status}</Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
