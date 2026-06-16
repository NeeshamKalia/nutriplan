import { useState, useEffect } from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Input } from '../../components/ui/Input';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Modal } from '../../components/ui/Modal';
import { protocolsApi, type Protocol, type ProtocolCreatePayload } from '../../api/protocols';
import './ProtocolsPage.css';

const EMPTY_FORM: ProtocolCreatePayload = {
  name: '',
  description: '',
  general_guidelines: '',
  target_conditions: [],
  target_goals: [],
  preferred_foods: [],
  avoided_foods: [],
};

function parseTags(value: string): string[] {
  return value
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean);
}

function joinTags(values?: string[] | null): string {
  return values?.join(', ') ?? '';
}

export function ProtocolsPage() {
  const [protocols, setProtocols] = useState<Protocol[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<Protocol | null>(null);
  const [form, setForm] = useState<ProtocolCreatePayload>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const fetchProtocols = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      const data = await protocolsApi.list(params);
      setProtocols(data.protocols);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load protocols', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProtocols();
  }, []);

  useEffect(() => {
    const timer = setTimeout(fetchProtocols, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const openCreate = () => {
    setEditing(null);
    setForm(EMPTY_FORM);
    setModalOpen(true);
  };

  const openEdit = (protocol: Protocol) => {
    setEditing(protocol);
    setForm({
      name: protocol.name,
      description: protocol.description ?? '',
      general_guidelines: protocol.general_guidelines ?? '',
      target_conditions: protocol.target_conditions ?? [],
      target_goals: protocol.target_goals ?? [],
      calorie_range_min: protocol.calorie_range_min ?? undefined,
      calorie_range_max: protocol.calorie_range_max ?? undefined,
      preferred_foods: protocol.preferred_foods ?? [],
      avoided_foods: protocol.avoided_foods ?? [],
    });
    setModalOpen(true);
  };

  const handleSave = async () => {
    if (!form.name.trim()) return;
    setSaving(true);
    try {
      if (editing) {
        await protocolsApi.update(editing.id, form);
      } else {
        await protocolsApi.create(form);
      }
      setModalOpen(false);
      fetchProtocols();
    } catch (err) {
      console.error('Failed to save protocol', err);
      window.alert('Failed to save protocol.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (protocol: Protocol) => {
    if (!window.confirm(`Delete protocol "${protocol.name}"?`)) return;
    try {
      await protocolsApi.delete(protocol.id);
      fetchProtocols();
    } catch (err) {
      console.error('Failed to delete protocol', err);
    }
  };

  return (
    <div className="protocols-page">
      <div className="protocols-page__header">
        <div>
          <h1 className="protocols-page__title">Protocols</h1>
          <p className="text-muted text-sm">
            Reusable meal plan templates for AI generation — e.g. PCOS, diabetes, weight loss.
          </p>
        </div>
        <Button variant="primary" onClick={openCreate}>New Protocol</Button>
      </div>

      <div className="protocols-page__filters">
        <div className="protocols-page__search">
          <Input
            label="Search"
            placeholder="Search by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {loading ? (
        <div className="protocols-page__loading">
          <LoadingSpinner size="lg" />
        </div>
      ) : protocols.length === 0 ? (
        <Card className="protocols-page__empty">
          <h3>No protocols yet</h3>
          <p className="text-muted">
            Create a template manually, or save an approved plan from the plan editor.
          </p>
          <Button variant="primary" onClick={openCreate}>Create Protocol</Button>
        </Card>
      ) : (
        <div className="protocols-page__grid">
          {protocols.map((protocol) => (
            <Card key={protocol.id} className="protocol-card">
              <div className="protocol-card__header">
                <h3>{protocol.name}</h3>
                {protocol.is_active ? (
                  <Badge variant="success">Active</Badge>
                ) : (
                  <Badge variant="warning">Inactive</Badge>
                )}
              </div>
              {protocol.description && (
                <p className="protocol-card__description">{protocol.description}</p>
              )}
              <div className="protocol-card__meta">
                {protocol.target_conditions?.length ? (
                  <span>Conditions: {protocol.target_conditions.join(', ')}</span>
                ) : null}
                {protocol.calorie_range_min || protocol.calorie_range_max ? (
                  <span>
                    Calories: {protocol.calorie_range_min ?? '?'}–{protocol.calorie_range_max ?? '?'} kcal
                  </span>
                ) : null}
                {protocol.sample_plan ? <span>Includes sample plan</span> : null}
              </div>
              {protocol.general_guidelines && (
                <p className="protocol-card__guidelines">{protocol.general_guidelines}</p>
              )}
              <div className="protocol-card__actions">
                <Button variant="secondary" onClick={() => openEdit(protocol)}>Edit</Button>
                <Button variant="ghost" onClick={() => handleDelete(protocol)}>Delete</Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <p className="protocols-page__count text-muted text-sm">{total} protocol{total === 1 ? '' : 's'}</p>

      <Modal
        isOpen={modalOpen}
        onClose={() => !saving && setModalOpen(false)}
        title={editing ? 'Edit Protocol' : 'New Protocol'}
      >
        <div className="protocol-form">
          <Input
            label="Name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="PCOS Weight Loss - Moderate Activity"
          />
          <Input
            label="Description"
            value={form.description ?? ''}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            placeholder="Short summary for your reference"
          />
          <Input
            label="General guidelines for AI"
            value={form.general_guidelines ?? ''}
            onChange={(e) => setForm({ ...form, general_guidelines: e.target.value })}
            placeholder="Focus on low-GI foods, 5 small meals..."
          />
          <Input
            label="Target conditions (comma-separated)"
            value={joinTags(form.target_conditions)}
            onChange={(e) => setForm({ ...form, target_conditions: parseTags(e.target.value) })}
            placeholder="PCOS, insulin resistance"
          />
          <Input
            label="Target goals (comma-separated)"
            value={joinTags(form.target_goals)}
            onChange={(e) => setForm({ ...form, target_goals: parseTags(e.target.value) })}
            placeholder="weight_loss, muscle_gain"
          />
          <div className="protocol-form__row">
            <Input
              label="Min calories"
              type="number"
              value={form.calorie_range_min?.toString() ?? ''}
              onChange={(e) =>
                setForm({
                  ...form,
                  calorie_range_min: e.target.value ? Number(e.target.value) : undefined,
                })
              }
            />
            <Input
              label="Max calories"
              type="number"
              value={form.calorie_range_max?.toString() ?? ''}
              onChange={(e) =>
                setForm({
                  ...form,
                  calorie_range_max: e.target.value ? Number(e.target.value) : undefined,
                })
              }
            />
          </div>
          <Input
            label="Preferred foods (comma-separated)"
            value={joinTags(form.preferred_foods)}
            onChange={(e) => setForm({ ...form, preferred_foods: parseTags(e.target.value) })}
          />
          <Input
            label="Avoided foods (comma-separated)"
            value={joinTags(form.avoided_foods)}
            onChange={(e) => setForm({ ...form, avoided_foods: parseTags(e.target.value) })}
          />
          <div className="protocol-form__actions">
            <Button variant="ghost" onClick={() => setModalOpen(false)} disabled={saving}>
              Cancel
            </Button>
            <Button variant="primary" onClick={handleSave} disabled={saving || !form.name.trim()}>
              {saving ? 'Saving...' : editing ? 'Save Changes' : 'Create Protocol'}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
