import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { progressApi, type ProgressLog } from '../../api/progress';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Modal } from '../ui/Modal';
import { LoadingSpinner } from '../ui/LoadingSpinner';
import { useToast } from '../../contexts/ToastContext';

export function ProgressTab({ clientId, startWeight }: { clientId: string, startWeight?: number }) {
  const [logs, setLogs] = useState<ProgressLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const toast = useToast();
  const [formData, setFormData] = useState({
    log_date: new Date().toISOString().split('T')[0],
    weight_kg: '',
    waist_cm: '',
    notes: ''
  });

  useEffect(() => {
    fetchLogs();
  }, [clientId]);

  const fetchLogs = async () => {
    try {
      const data = await progressApi.getLogs(clientId);
      setLogs(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await progressApi.logProgress(clientId, {
        log_date: formData.log_date,
        weight_kg: formData.weight_kg ? parseFloat(formData.weight_kg) : undefined,
        waist_cm: formData.waist_cm ? parseFloat(formData.waist_cm) : undefined,
        notes: formData.notes || undefined
      });
      setIsModalOpen(false);
      setFormData({ log_date: new Date().toISOString().split('T')[0], weight_kg: '', waist_cm: '', notes: '' });
      fetchLogs();
    } catch (err) {
      console.error(err);
      toast.error('Log failed', 'Failed to log progress.');
    }
  };

  const chartData = logs.map(log => ({
    date: log.log_date,
    Weight: log.weight_kg
  }));

  const logWithWeight = [...logs].reverse().find(log => log.weight_kg !== undefined && log.weight_kg !== null);
  const currentWeight = logWithWeight ? logWithWeight.weight_kg : startWeight;
  const delta = startWeight && currentWeight ? (currentWeight - startWeight).toFixed(1) : null;
  const deltaText = delta ? (parseFloat(delta) > 0 ? `↑ ${delta} kg` : `↓ ${Math.abs(parseFloat(delta))} kg`) : 'No change';

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: '2rem' }}>
          <div>
            <p className="text-muted text-sm">Starting Weight</p>
            <p className="font-semibold text-lg">{startWeight ? `${startWeight} kg` : '-'}</p>
          </div>
          <div>
            <p className="text-muted text-sm">Current Weight</p>
            <p className="font-semibold text-lg">{currentWeight ? `${currentWeight} kg` : '-'}</p>
          </div>
          {delta && (
            <div>
              <p className="text-muted text-sm">Change</p>
              <p className={`font-semibold text-lg ${parseFloat(delta) > 0 ? 'text-red-500' : 'text-green-500'}`}>
                {deltaText}
              </p>
            </div>
          )}
        </div>
        <Button onClick={() => setIsModalOpen(true)}>Log Progress</Button>
      </div>

      <Card>
        <h3 className="font-semibold mb-4">Weight History</h3>
        {logs.length === 0 ? (
          <p className="text-muted text-center py-8">No progress logs yet.</p>
        ) : (
          <div style={{ height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                <XAxis dataKey="date" stroke="var(--text-muted)" />
                <YAxis stroke="var(--text-muted)" domain={['auto', 'auto']} />
                <Tooltip 
                  contentStyle={{ backgroundColor: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '8px' }}
                />
                <Line type="monotone" dataKey="Weight" stroke="var(--color-primary-600)" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      <Card>
        <h3 className="font-semibold mb-4">Log Entries</h3>
        {logs.length === 0 ? (
          <p className="text-muted text-center py-4">No entries.</p>
        ) : (
          <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)' }}>
                <th style={{ padding: '0.75rem' }}>Date</th>
                <th style={{ padding: '0.75rem' }}>Weight (kg)</th>
                <th style={{ padding: '0.75rem' }}>Waist (cm)</th>
                <th style={{ padding: '0.75rem' }}>Notes</th>
              </tr>
            </thead>
            <tbody>
              {logs.map(log => (
                <tr key={log.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '0.75rem' }}>{log.log_date}</td>
                  <td style={{ padding: '0.75rem' }}>{log.weight_kg || '-'}</td>
                  <td style={{ padding: '0.75rem' }}>{log.waist_cm || '-'}</td>
                  <td style={{ padding: '0.75rem', color: 'var(--text-muted)' }}>{log.notes || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title="Log Progress">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input 
            label="Date" 
            type="date" 
            required 
            value={formData.log_date}
            onChange={e => setFormData({...formData, log_date: e.target.value})}
          />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input 
              label="Weight (kg)" 
              type="number" 
              step="0.1"
              value={formData.weight_kg}
              onChange={e => setFormData({...formData, weight_kg: e.target.value})}
            />
            <Input 
              label="Waist (cm)" 
              type="number" 
              step="0.1"
              value={formData.waist_cm}
              onChange={e => setFormData({...formData, waist_cm: e.target.value})}
            />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.875rem', fontWeight: 500 }}>Notes</label>
            <textarea
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem',
                borderRadius: '0.375rem',
                border: '1px solid var(--border-color)',
                backgroundColor: 'var(--bg-input, transparent)',
                color: 'inherit',
                minHeight: '80px',
                fontFamily: 'inherit'
              }}
              placeholder="How are you feeling?"
              value={formData.notes}
              onChange={e => setFormData({...formData, notes: e.target.value})}
            />
          </div>
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1.5rem' }}>
            <Button variant="ghost" type="button" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button variant="primary" type="submit">Save Log</Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
