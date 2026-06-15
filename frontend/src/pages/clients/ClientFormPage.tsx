import { useState, useEffect, type FormEvent } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../api/client';
import { Card } from '../../components/ui/Card';
import { Input, Textarea } from '../../components/ui/Input';
import { Button } from '../../components/ui/Button';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';

export function ClientFormPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const isEditMode = !!id;

  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(isEditMode);
  const [error, setError] = useState('');

  const [formData, setFormData] = useState({
    full_name: '',
    whatsapp_number: '',
    email: '',
    age: '',
    gender: 'female',
    height_cm: '',
    weight_kg: '',
    target_weight_kg: '',
    activity_level: 'light',
    dietary_type: 'veg',
    cuisine_preference: 'north_indian',
    primary_goal: 'weight_loss',
    monthly_food_budget_inr: '',
    medical_conditions: '',
    allergies: '',
    food_preferences: '',
    daily_calorie_target: '',
    meals_per_day: '4',
    lifestyle_notes: '',
    notes: ''
  });

  useEffect(() => {
    if (isEditMode) {
      const fetchClient = async () => {
        try {
          const { data } = await api.get(`/clients/${id}`);
          setFormData({
            full_name: data.full_name || '',
            whatsapp_number: data.whatsapp_number || '',
            email: data.email || '',
            age: data.age?.toString() || '',
            gender: data.gender || 'female',
            height_cm: data.height_cm?.toString() || '',
            weight_kg: data.weight_kg?.toString() || '',
            target_weight_kg: data.target_weight_kg?.toString() || '',
            activity_level: data.activity_level || 'light',
            dietary_type: data.dietary_type || 'veg',
            cuisine_preference: data.cuisine_preference || 'north_indian',
            primary_goal: data.primary_goal || 'weight_loss',
            monthly_food_budget_inr: data.monthly_food_budget_inr?.toString() || '',
            medical_conditions: data.medical_conditions?.join(', ') || '',
            allergies: data.allergies?.join(', ') || '',
            food_preferences: data.food_preferences?.join(', ') || '',
            daily_calorie_target: data.daily_calorie_target?.toString() || '',
            meals_per_day: data.meals_per_day?.toString() || '4',
            lifestyle_notes: data.lifestyle_notes || '',
            notes: data.notes || ''
          });
        } catch (err: any) {
          setError('Failed to fetch client details');
        } finally {
          setIsFetching(false);
        }
      };
      fetchClient();
    }
  }, [id, isEditMode]);

  const handleChange = (e: any) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const payload = {
        ...formData,
        age: formData.age ? parseInt(formData.age) : null,
        height_cm: formData.height_cm ? parseFloat(formData.height_cm) : null,
        weight_kg: formData.weight_kg ? parseFloat(formData.weight_kg) : null,
        target_weight_kg: formData.target_weight_kg ? parseFloat(formData.target_weight_kg) : null,
        monthly_food_budget_inr: formData.monthly_food_budget_inr ? parseInt(formData.monthly_food_budget_inr) : null,
        daily_calorie_target: formData.daily_calorie_target ? parseInt(formData.daily_calorie_target) : null,
        meals_per_day: formData.meals_per_day ? parseInt(formData.meals_per_day) : 4,
        medical_conditions: formData.medical_conditions ? formData.medical_conditions.split(',').map(s => s.trim()).filter(Boolean) : [],
        allergies: formData.allergies ? formData.allergies.split(',').map(s => s.trim()).filter(Boolean) : [],
        food_preferences: formData.food_preferences ? formData.food_preferences.split(',').map(s => s.trim()).filter(Boolean) : [],
      };

      if (isEditMode) {
        await api.put(`/clients/${id}`, payload);
        navigate(`/clients/${id}`);
      } else {
        const { data } = await api.post('/clients', payload);
        navigate(`/clients/${data.id}`);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to ${isEditMode ? 'update' : 'create'} client`);
    } finally {
      setIsLoading(false);
    }
  };

  if (isFetching) {
    return <div className="p-8 text-center"><LoadingSpinner /></div>;
  }

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold mb-2">{isEditMode ? 'Edit Client' : 'Add New Client'}</h1>
        <p className="text-muted">{isEditMode ? 'Update client profile details.' : 'Create a comprehensive health profile.'}</p>
      </div>

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md text-sm border border-red-200">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        <Card>
          <h2 className="font-semibold text-lg mb-4">Personal Details</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Input label="Full Name *" name="full_name" value={formData.full_name} onChange={handleChange} required />
            <Input label="WhatsApp Number *" name="whatsapp_number" value={formData.whatsapp_number} onChange={handleChange} required placeholder="+91..." />
            <Input label="Email Address" type="email" name="email" value={formData.email} onChange={handleChange} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <Input label="Age" type="number" name="age" value={formData.age} onChange={handleChange} />
              <div>
                <label className="input-group__label" style={{ display: 'block', marginBottom: '0.25rem' }}>Gender</label>
                <select name="gender" value={formData.gender} onChange={handleChange} className="input-group__input">
                  <option value="female">Female</option>
                  <option value="male">Male</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>
          </div>
        </Card>

        <Card>
          <h2 className="font-semibold text-lg mb-4">Body Metrics & Goals</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
            <Input label="Height (cm)" type="number" name="height_cm" value={formData.height_cm} onChange={handleChange} />
            <Input label="Weight (kg)" type="number" step="0.1" name="weight_kg" value={formData.weight_kg} onChange={handleChange} />
            <Input label="Target (kg)" type="number" step="0.1" name="target_weight_kg" value={formData.target_weight_kg} onChange={handleChange} />
            <Input label="Daily Kcal Target" type="number" name="daily_calorie_target" value={formData.daily_calorie_target} onChange={handleChange} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
            <div>
              <label className="input-group__label" style={{ display: 'block', marginBottom: '0.25rem' }}>Activity</label>
              <select name="activity_level" value={formData.activity_level} onChange={handleChange} className="input-group__input">
                <option value="sedentary">Sedentary</option>
                <option value="light">Light</option>
                <option value="moderate">Moderate</option>
                <option value="active">Active</option>
                <option value="very_active">Very Active</option>
              </select>
            </div>
            <div>
              <label className="input-group__label" style={{ display: 'block', marginBottom: '0.25rem' }}>Primary Goal</label>
              <select name="primary_goal" value={formData.primary_goal} onChange={handleChange} className="input-group__input">
                <option value="weight_loss">Weight Loss</option>
                <option value="weight_gain">Weight Gain</option>
                <option value="maintenance">Maintenance</option>
                <option value="clinical_management">Clinical Management</option>
                <option value="muscle_gain">Muscle Gain</option>
              </select>
            </div>
          </div>
        </Card>

        <Card>
          <h2 className="font-semibold text-lg mb-4">Health & Preferences</h2>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label className="input-group__label" style={{ display: 'block', marginBottom: '0.25rem' }}>Dietary Type</label>
              <select name="dietary_type" value={formData.dietary_type} onChange={handleChange} className="input-group__input">
                <option value="veg">Vegetarian</option>
                <option value="non_veg">Non-Vegetarian</option>
                <option value="vegan">Vegan</option>
                <option value="eggetarian">Eggetarian</option>
              </select>
            </div>
            <div>
              <label className="input-group__label" style={{ display: 'block', marginBottom: '0.25rem' }}>Meals Per Day</label>
              <select name="meals_per_day" value={formData.meals_per_day} onChange={handleChange} className="input-group__input">
                <option value="3">3</option>
                <option value="4">4</option>
                <option value="5">5</option>
                <option value="6">6</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <Input label="Food Preferences" name="food_preferences" value={formData.food_preferences} onChange={handleChange} hint="Comma separated (e.g. Paneer, Rice)" />
            <Input label="Allergies" name="allergies" value={formData.allergies} onChange={handleChange} hint="Comma separated (e.g. Peanuts, Dairy)" />
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <Input label="Medical Conditions" name="medical_conditions" value={formData.medical_conditions} onChange={handleChange} hint="Comma separated (e.g. PCOS, Diabetes)" />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <Textarea label="Lifestyle Notes" name="lifestyle_notes" value={formData.lifestyle_notes} onChange={handleChange} placeholder="Sleep, stress, exercise routine..." />
            <Textarea label="Dietitian Notes" name="notes" value={formData.notes} onChange={handleChange} placeholder="Private notes visible only to you..." />
          </div>
        </Card>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
          <Button type="button" variant="ghost" onClick={() => navigate(isEditMode ? `/clients/${id}` : '/clients')}>Cancel</Button>
          <Button type="submit" isLoading={isLoading}>{isEditMode ? 'Update Client' : 'Save Client Profile'}</Button>
        </div>
      </form>
    </div>
  );
}
