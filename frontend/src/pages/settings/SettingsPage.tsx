/**
 * Settings Page — UX-001
 *
 * Three tabs: Profile, WhatsApp Setup, Account
 * Connects to PUT /api/v1/auth/me and PUT /api/v1/auth/me/whatsapp backend endpoints.
 */

import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input, Textarea } from '../../components/ui/Input';
import api from '../../api/client';
import './SettingsPage.css';

type Tab = 'profile' | 'whatsapp' | 'account';

interface ProfileForm {
  full_name: string;
  phone: string;
  bio: string;
  practice_name: string;
  qualifications: string;
  specializations: string;
}

interface WhatsAppForm {
  whatsapp_phone_number_id: string;
  whatsapp_access_token: string;
  whatsapp_business_account_id: string;
}

export function SettingsPage() {
  const { user, logout } = useAuth();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState<Tab>('profile');
  const [saving, setSaving] = useState(false);

  // Profile form state
  const [profile, setProfile] = useState<ProfileForm>({
    full_name: '',
    phone: '',
    bio: '',
    practice_name: '',
    qualifications: '',
    specializations: '',
  });

  // WhatsApp form state
  const [whatsapp, setWhatsApp] = useState<WhatsAppForm>({
    whatsapp_phone_number_id: '',
    whatsapp_access_token: '',
    whatsapp_business_account_id: '',
  });

  // Initialize form from user context
  useEffect(() => {
    if (user) {
      setProfile({
        full_name: user.full_name || '',
        phone: user.phone || '',
        bio: '',
        practice_name: user.practice_name || '',
        qualifications: '',
        specializations: user.specializations?.join(', ') || '',
      });

      // Fetch full profile (some fields not in context)
      api.get('/auth/me').then(({ data }) => {
        setProfile((prev) => ({
          ...prev,
          bio: data.bio || '',
          qualifications: data.qualifications || '',
        }));
      }).catch(() => {
        // Silent fail — we already have partial data from context
      });
    }
  }, [user]);

  const handleSaveProfile = async () => {
    setSaving(true);
    try {
      const payload: Record<string, any> = {
        full_name: profile.full_name,
        phone: profile.phone || null,
        bio: profile.bio || null,
        practice_name: profile.practice_name || null,
        qualifications: profile.qualifications || null,
      };

      // Convert comma-separated specializations to array
      if (profile.specializations.trim()) {
        payload.specializations = profile.specializations
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean);
      } else {
        payload.specializations = null;
      }

      await api.put('/auth/me', payload);
      toast.success('Profile updated', 'Your practice profile has been saved.');
    } catch (err: any) {
      toast.error('Update failed', err.response?.data?.detail || 'Could not save profile.');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveWhatsApp = async () => {
    if (!whatsapp.whatsapp_phone_number_id || !whatsapp.whatsapp_access_token) {
      toast.warning('Missing fields', 'Phone Number ID and Access Token are required.');
      return;
    }

    setSaving(true);
    try {
      await api.put('/auth/me/whatsapp', whatsapp);
      toast.success('WhatsApp connected', 'Your WhatsApp Business credentials have been saved.');
    } catch (err: any) {
      toast.error('Setup failed', err.response?.data?.detail || 'Could not save WhatsApp credentials.');
    } finally {
      setSaving(false);
    }
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'profile', label: 'Practice Profile' },
    { key: 'whatsapp', label: 'WhatsApp Setup' },
    { key: 'account', label: 'Account' },
  ];

  return (
    <div className="settings-page">
      <div className="settings-page__header">
        <h1 className="settings-page__title">Settings</h1>
        <p className="settings-page__subtitle">Manage your practice profile and integrations.</p>
      </div>

      <div className="settings-tabs" role="tablist">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            role="tab"
            aria-selected={activeTab === tab.key}
            className={`settings-tab ${activeTab === tab.key ? 'settings-tab--active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <Card>
          <div className="settings-section">
            <h2 className="settings-section__title">Practice Profile</h2>
            <p className="settings-section__description">
              This information appears on your public landing page and client communications.
            </p>
          </div>

          <div className="settings-form">
            <div className="settings-form__row">
              <Input
                id="settings-full-name"
                label="Full Name"
                value={profile.full_name}
                onChange={(e) => setProfile((p) => ({ ...p, full_name: e.target.value }))}
                placeholder="Dr. Neha Sharma"
              />
              <Input
                id="settings-phone"
                label="Phone"
                value={profile.phone}
                onChange={(e) => setProfile((p) => ({ ...p, phone: e.target.value }))}
                placeholder="+91 98765 43210"
              />
            </div>

            <Input
              id="settings-practice-name"
              label="Practice Name"
              value={profile.practice_name}
              onChange={(e) => setProfile((p) => ({ ...p, practice_name: e.target.value }))}
              placeholder="NutriWell Clinic"
            />

            <Input
              id="settings-qualifications"
              label="Qualifications"
              value={profile.qualifications}
              onChange={(e) => setProfile((p) => ({ ...p, qualifications: e.target.value }))}
              placeholder="M.Sc. Nutrition, Certified Dietitian"
            />

            <Input
              id="settings-specializations"
              label="Specializations"
              value={profile.specializations}
              onChange={(e) => setProfile((p) => ({ ...p, specializations: e.target.value }))}
              hint="Comma-separated: Weight Loss, PCOS, Diabetes Management"
            />

            <Textarea
              id="settings-bio"
              label="Bio"
              value={profile.bio}
              onChange={(e) => setProfile((p) => ({ ...p, bio: e.target.value }))}
              placeholder="Tell your clients about yourself and your approach..."
              rows={4}
            />

            <div className="settings-form__actions">
              <Button
                variant="primary"
                onClick={handleSaveProfile}
                isLoading={saving}
              >
                Save Profile
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* WhatsApp Tab */}
      {activeTab === 'whatsapp' && (
        <Card>
          <div className="settings-section">
            <h2 className="settings-section__title">WhatsApp Business Setup</h2>
            <p className="settings-section__description">
              Connect your WhatsApp Business account to send meal plans and
              receive client messages. You'll need your Meta Business API credentials.
            </p>
          </div>

          <div className={`whatsapp-status ${user?.has_whatsapp_setup ? 'whatsapp-status--connected' : 'whatsapp-status--disconnected'}`}>
            <span className="whatsapp-status__icon">
              {user?.has_whatsapp_setup ? '✅' : '⚠️'}
            </span>
            <span className="whatsapp-status__text">
              {user?.has_whatsapp_setup
                ? 'WhatsApp is connected and ready to send messages.'
                : 'WhatsApp is not connected. Add your credentials below to enable messaging.'}
            </span>
          </div>

          <div className="settings-form">
            <Input
              id="settings-wa-phone-id"
              label="Phone Number ID"
              value={whatsapp.whatsapp_phone_number_id}
              onChange={(e) =>
                setWhatsApp((w) => ({ ...w, whatsapp_phone_number_id: e.target.value }))
              }
              placeholder="e.g., 123456789012345"
              hint="Found in your Meta Business Manager under WhatsApp > API Setup"
            />

            <Input
              id="settings-wa-access-token"
              label="Access Token"
              type="password"
              value={whatsapp.whatsapp_access_token}
              onChange={(e) =>
                setWhatsApp((w) => ({ ...w, whatsapp_access_token: e.target.value }))
              }
              placeholder="Your permanent access token"
              hint="Generate a permanent token in Meta Business Manager. This will be encrypted at rest."
            />

            <Input
              id="settings-wa-business-id"
              label="Business Account ID (Optional)"
              value={whatsapp.whatsapp_business_account_id}
              onChange={(e) =>
                setWhatsApp((w) => ({ ...w, whatsapp_business_account_id: e.target.value }))
              }
              placeholder="e.g., 987654321098765"
            />

            <div className="settings-form__actions">
              <Button
                variant="primary"
                onClick={handleSaveWhatsApp}
                isLoading={saving}
              >
                Save WhatsApp Credentials
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Account Tab */}
      {activeTab === 'account' && (
        <Card>
          <div className="settings-section">
            <h2 className="settings-section__title">Account</h2>
            <p className="settings-section__description">
              Manage your account settings.
            </p>
          </div>

          <div className="settings-form">
            <Input
              id="settings-email"
              label="Email"
              value={user?.email || ''}
              disabled
              hint="Contact support to change your email address."
            />

            <Input
              id="settings-slug"
              label="Public URL Slug"
              value={user?.slug || ''}
              disabled
              hint={`Your landing page: ${window.location.origin}/p/${user?.slug || ''}`}
            />

            <div className="settings-form__actions">
              <Button variant="danger" onClick={logout}>
                Sign Out
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
