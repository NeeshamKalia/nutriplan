import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../api/client';
import type { Client, ClientListResponse } from '../../types/client';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Badge } from '../../components/ui/Badge';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { EmptyState } from '../../components/ui/EmptyState';

export function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  
  const navigate = useNavigate();

  const fetchClients = useCallback(async () => {
    try {
      setIsLoading(true);
      const { data } = await api.get<ClientListResponse>('/clients', {
        params: { search, status, limit: 20, offset: 0 }
      });
      setClients(data.clients);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to fetch clients', err);
    } finally {
      setIsLoading(false);
    }
  }, [search, status]);

  useEffect(() => {
    // Debounce search
    const timer = setTimeout(() => {
      fetchClients();
    }, 300);
    return () => clearTimeout(timer);
  }, [fetchClients]);

  const getStatusBadge = (s: string) => {
    switch (s) {
      case 'active': return <Badge variant="success">Active</Badge>;
      case 'paused': return <Badge variant="warning">Paused</Badge>;
      case 'archived': return <Badge variant="default">Archived</Badge>;
      default: return <Badge>{s}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 className="text-2xl font-bold mb-2">Clients ({total})</h1>
          <p className="text-muted">Manage your clients and health profiles.</p>
        </div>
        <Button onClick={() => navigate('/clients/new')}>Add Client</Button>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem' }}>
        <Input 
          placeholder="Search by name..." 
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ flex: 1, maxWidth: '300px' }}
        />
        <select 
          value={status} 
          onChange={(e) => setStatus(e.target.value)}
          className="input-group__input"
          style={{ width: '150px' }}
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="paused">Paused</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {isLoading ? (
        <div style={{ padding: '3rem 0', display: 'flex', justifyContent: 'center' }}>
          <LoadingSpinner />
        </div>
      ) : clients.length === 0 ? (
        <Card>
          <EmptyState
            icon="👥"
            title="No clients found"
            description={
              search || status
                ? 'No clients match your current search or filter. Try adjusting your criteria.'
                : 'Add your first client to start creating personalized meal plans and tracking their progress.'
            }
            actionLabel={!search && !status ? 'Add your first client' : undefined}
            onAction={!search && !status ? () => navigate('/clients/new') : undefined}
          />
        </Card>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' }}>
          {clients.map(client => (
            <Card key={client.id} hover onClick={() => navigate(`/clients/${client.id}`)} style={{ cursor: 'pointer' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                  <h3 className="font-semibold text-lg">{client.full_name}</h3>
                  <p className="text-muted text-sm">{client.whatsapp_number}</p>
                </div>
                {getStatusBadge(client.status)}
              </div>
              
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                {client.primary_goal && (
                  <Badge variant="info">{client.primary_goal.replace('_', ' ')}</Badge>
                )}
                {client.dietary_type && (
                  <Badge variant="default">{client.dietary_type}</Badge>
                )}
              </div>

              {client.medical_conditions && client.medical_conditions.length > 0 && (
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {client.medical_conditions.map(cond => (
                    <Badge key={cond} variant="warning">{cond}</Badge>
                  ))}
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
