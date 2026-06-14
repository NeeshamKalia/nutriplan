import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../../api/client';
import type { Client } from '../../types/client';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { plansApi } from '../../api/plans';
import type { MealPlan } from '../../types/plan';

export function ClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [client, setClient] = useState<Client | null>(null);
  const [plans, setPlans] = useState<MealPlan[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'profile' | 'plans' | 'progress' | 'adherence'>('profile');

  const handleCreatePlan = async () => {
    try {
      const startOfWeek = new Date(); // e.g., today
      const newPlan = await plansApi.createPlan(id!, {
        title: 'New Meal Plan',
        week_start_date: startOfWeek.toISOString().split('T')[0],
        days: Array.from({ length: 7 }).map((_, i) => ({
          day_number: i + 1,
          day_label: `Day ${i + 1}`,
          items: []
        }))
      });
      navigate(`/plans/${newPlan.id}`);
    } catch (err) {
      alert('Failed to create plan.');
    }
  };

  useEffect(() => {
    async function fetchClient() {
      try {
        const [clientRes, plansRes] = await Promise.all([
          api.get<Client>(`/clients/${id}`),
          plansApi.getPlansByClient(id!)
        ]);
        setClient(clientRes.data);
        setPlans(plansRes.items || []);
      } catch (err) {
        console.error('Failed to fetch client data', err);
        navigate('/clients');
      } finally {
        setIsLoading(false);
      }
    }
    fetchClient();
  }, [id, navigate]);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!client) return null;

  return (
    <div className="space-y-6">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
            <h1 className="text-3xl font-bold">{client.full_name}</h1>
            <Badge variant={client.status === 'active' ? 'success' : 'default'}>{client.status}</Badge>
          </div>
          <p className="text-muted">{client.whatsapp_number} {client.email ? `• ${client.email}` : ''}</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <Button variant="secondary" onClick={() => navigate(`/clients/${id}/edit`)}>Edit Profile</Button>
          <Button variant="primary" onClick={handleCreatePlan}>Create Blank Plan</Button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '2rem', borderBottom: '1px solid var(--border-color)', marginBottom: '2rem' }}>
        {['profile', 'plans', 'progress', 'adherence'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab as any)}
            style={{
              background: 'none',
              border: 'none',
              padding: '1rem 0',
              fontWeight: activeTab === tab ? '600' : '500',
              color: activeTab === tab ? 'var(--color-primary-600)' : 'var(--text-muted)',
              borderBottom: activeTab === tab ? '2px solid var(--color-primary-600)' : '2px solid transparent',
              cursor: 'pointer',
              textTransform: 'capitalize'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'profile' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
          <Card>
            <h3 className="font-semibold mb-4">Personal Details</h3>
            <dl style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '0.75rem' }}>
              <dt className="text-muted">Age</dt><dd>{client.age || '-'}</dd>
              <dt className="text-muted">Gender</dt><dd style={{ textTransform: 'capitalize' }}>{client.gender || '-'}</dd>
              <dt className="text-muted">Height</dt><dd>{client.height_cm ? `${client.height_cm} cm` : '-'}</dd>
              <dt className="text-muted">Weight</dt><dd>{client.weight_kg ? `${client.weight_kg} kg` : '-'}</dd>
              <dt className="text-muted">Target Weight</dt><dd>{client.target_weight_kg ? `${client.target_weight_kg} kg` : '-'}</dd>
              <dt className="text-muted">Activity</dt><dd style={{ textTransform: 'capitalize' }}>{client.activity_level ? client.activity_level.replace('_', ' ') : '-'}</dd>
            </dl>
          </Card>

          <Card>
            <h3 className="font-semibold mb-4">Health & Preferences</h3>
            <dl style={{ display: 'grid', gridTemplateColumns: '120px 1fr', gap: '0.75rem' }}>
              <dt className="text-muted">Diet</dt><dd style={{ textTransform: 'capitalize' }}>{client.dietary_type || '-'}</dd>
              <dt className="text-muted">Goal</dt><dd style={{ textTransform: 'capitalize' }}>{client.primary_goal ? client.primary_goal.replace('_', ' ') : '-'}</dd>
              <dt className="text-muted">Cuisine</dt><dd style={{ textTransform: 'capitalize' }}>{client.cuisine_preference ? client.cuisine_preference.replace('_', ' ') : '-'}</dd>
              <dt className="text-muted">Conditions</dt>
              <dd>
                {client.medical_conditions?.length ? (
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {client.medical_conditions.map(c => <Badge key={c} variant="warning">{c}</Badge>)}
                  </div>
                ) : '-'}
              </dd>
              <dt className="text-muted">Allergies</dt>
              <dd>
                {client.allergies?.length ? (
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {client.allergies.map(c => <Badge key={c} variant="danger">{c}</Badge>)}
                  </div>
                ) : '-'}
              </dd>
            </dl>
          </Card>

          {client.notes && (
            <Card style={{ gridColumn: '1 / -1' }}>
              <h3 className="font-semibold mb-2">Notes</h3>
              <p style={{ whiteSpace: 'pre-wrap' }}>{client.notes}</p>
            </Card>
          )}
        </div>
      )}

      {activeTab === 'plans' && (
        <Card>
          {plans.length === 0 ? (
            <div style={{ padding: '3rem', textAlign: 'center' }}>
              <h3 className="font-semibold text-lg mb-2">No Meal Plans</h3>
              <p className="text-muted mb-4">Create a blank plan or generate one with AI.</p>
              <Button onClick={handleCreatePlan}>Create Blank Plan</Button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {plans.map(plan => (
                <div key={plan.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1rem', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                  <div>
                    <h4 className="font-semibold">{plan.title || 'Untitled Plan'}</h4>
                    <p className="text-muted text-sm">Starts: {plan.week_start_date}</p>
                  </div>
                  <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <Badge variant={plan.status === 'draft' ? 'warning' : 'success'}>{plan.status}</Badge>
                    <Button variant="secondary" onClick={() => navigate(`/plans/${plan.id}`)}>View / Edit</Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      )}

      {(activeTab === 'progress' || activeTab === 'adherence') && (
        <Card>
          <div style={{ padding: '3rem', textAlign: 'center' }}>
            <h3 className="font-semibold text-lg mb-2">Coming Soon</h3>
            <p className="text-muted">This feature will be available in a future phase.</p>
          </div>
        </Card>
      )}
    </div>
  );
}
