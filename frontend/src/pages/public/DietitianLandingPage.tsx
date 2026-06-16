import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { Button } from '../../components/ui/Button';
import { Input, Textarea } from '../../components/ui/Input';
import { publicApi, type DietitianPublicProfile, type Article } from '../../api/articles';
import './PublicPages.css';

function buildWhatsAppUrl(phone: string, message: string): string {
  const digits = phone.replace(/\D/g, '');
  return `https://wa.me/${digits}?text=${encodeURIComponent(message)}`;
}

export function DietitianLandingPage() {
  const { slug } = useParams<{ slug: string }>();
  const [dietitian, setDietitian] = useState<DietitianPublicProfile | null>(null);
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [intakeName, setIntakeName] = useState('');
  const [intakePhone, setIntakePhone] = useState('');
  const [intakeGoal, setIntakeGoal] = useState('');
  const [intakeDiet, setIntakeDiet] = useState('');
  const [intakeNotes, setIntakeNotes] = useState('');
  const [intakeSubmitting, setIntakeSubmitting] = useState(false);
  const [intakeSuccess, setIntakeSuccess] = useState('');
  const [intakeError, setIntakeError] = useState('');

  useEffect(() => {
    if (!slug) return;
    const fetchData = async () => {
      try {
        const [profile, arts] = await Promise.all([
          publicApi.getDietitian(slug),
          publicApi.getArticles(slug),
        ]);
        setDietitian(profile);
        setArticles(arts);
      } catch {
        setError('Dietitian not found.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [slug]);

  const handleIntakeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!slug) return;
    setIntakeError('');
    setIntakeSuccess('');
    setIntakeSubmitting(true);
    try {
      const result = await publicApi.submitIntake(slug, {
        full_name: intakeName.trim(),
        whatsapp_number: intakePhone.trim(),
        primary_goal: intakeGoal || undefined,
        dietary_type: intakeDiet || undefined,
        notes: intakeNotes.trim() || undefined,
      });
      setIntakeSuccess(result.message);
      setIntakeName('');
      setIntakePhone('');
      setIntakeGoal('');
      setIntakeDiet('');
      setIntakeNotes('');
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined;
      setIntakeError(message || 'Could not submit form. Please try again.');
    } finally {
      setIntakeSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="public-page__loading">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !dietitian) {
    return (
      <div className="public-page__error">
        <h1>Not Found</h1>
        <p>{error || 'This page does not exist.'}</p>
      </div>
    );
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  };

  const pageTitle = dietitian.practice_name
    ? `${dietitian.full_name} — ${dietitian.practice_name}`
    : dietitian.full_name;
  const pageDescription = dietitian.bio
    ? dietitian.bio.slice(0, 160)
    : `${dietitian.full_name} — Nutritionist on NutriPlan`;

  const whatsappMessage = `Hi ${dietitian.full_name}, I found your page on NutriPlan and would like to know more about your nutrition programs.`;
  const whatsappUrl = dietitian.phone
    ? buildWhatsAppUrl(dietitian.phone, whatsappMessage)
    : null;

  return (
    <div className="public-page">
      <Helmet>
        <title>{pageTitle} | NutriPlan</title>
        <meta name="description" content={pageDescription} />
        <meta property="og:title" content={pageTitle} />
        <meta property="og:description" content={pageDescription} />
        <meta property="og:type" content="profile" />
        {dietitian.photo_url && <meta property="og:image" content={dietitian.photo_url} />}
      </Helmet>

      <header className="landing__header">
        <div className="landing__header-inner">
          <div className="landing__brand">
            <span className="landing__brand-name">NutriPlan</span>
          </div>
          {whatsappUrl && (
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="landing__whatsapp-cta"
            >
              Chat on WhatsApp
            </a>
          )}
        </div>
      </header>

      <section className="landing__hero">
        <div className="landing__hero-inner">
          {dietitian.photo_url && (
            <img
              src={dietitian.photo_url}
              alt={dietitian.full_name}
              className="landing__avatar"
            />
          )}
          {!dietitian.photo_url && (
            <div className="landing__avatar landing__avatar--placeholder">
              {dietitian.full_name.charAt(0)}
            </div>
          )}
          <h1 className="landing__name">{dietitian.full_name}</h1>
          {dietitian.practice_name && (
            <p className="landing__practice">{dietitian.practice_name}</p>
          )}
          {dietitian.qualifications && (
            <p className="landing__qualifications">{dietitian.qualifications}</p>
          )}
          {dietitian.specializations && dietitian.specializations.length > 0 && (
            <div className="landing__specializations">
              {dietitian.specializations.map((spec) => (
                <span key={spec} className="landing__spec-badge">
                  {spec}
                </span>
              ))}
            </div>
          )}
          {dietitian.bio && <p className="landing__bio">{dietitian.bio}</p>}
          {whatsappUrl && (
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="landing__whatsapp-hero"
            >
              Message on WhatsApp
            </a>
          )}
        </div>
      </section>

      <section className="landing__intake">
        <div className="landing__intake-inner">
          <h2 className="landing__section-title">Start Your Nutrition Journey</h2>
          <p className="landing__intake-subtitle">
            Fill in your details and {dietitian.full_name.split(' ')[0]} will reach out on WhatsApp.
          </p>

          {intakeSuccess && (
            <div className="landing__intake-success">{intakeSuccess}</div>
          )}
          {intakeError && (
            <div className="landing__intake-error">{intakeError}</div>
          )}

          <form className="landing__intake-form" onSubmit={handleIntakeSubmit}>
            <div className="landing__intake-grid">
              <Input
                label="Full Name"
                value={intakeName}
                onChange={(e) => setIntakeName(e.target.value)}
                required
                placeholder="Your name"
              />
              <Input
                label="WhatsApp Number"
                value={intakePhone}
                onChange={(e) => setIntakePhone(e.target.value)}
                required
                placeholder="10-digit mobile number"
              />
            </div>
            <div className="landing__intake-grid">
              <div className="landing__intake-field">
                <label className="landing__intake-label" htmlFor="intake-goal">
                  Primary Goal
                </label>
                <select
                  id="intake-goal"
                  className="landing__intake-select"
                  value={intakeGoal}
                  onChange={(e) => setIntakeGoal(e.target.value)}
                >
                  <option value="">Select a goal</option>
                  <option value="weight_loss">Weight Loss</option>
                  <option value="weight_gain">Weight Gain</option>
                  <option value="pcos">PCOS Management</option>
                  <option value="diabetes">Diabetes Management</option>
                  <option value="general_wellness">General Wellness</option>
                </select>
              </div>
              <div className="landing__intake-field">
                <label className="landing__intake-label" htmlFor="intake-diet">
                  Dietary Preference
                </label>
                <select
                  id="intake-diet"
                  className="landing__intake-select"
                  value={intakeDiet}
                  onChange={(e) => setIntakeDiet(e.target.value)}
                >
                  <option value="">Select preference</option>
                  <option value="vegetarian">Vegetarian</option>
                  <option value="vegan">Vegan</option>
                  <option value="eggetarian">Eggetarian</option>
                  <option value="non_vegetarian">Non-Vegetarian</option>
                </select>
              </div>
            </div>
            <Textarea
              label="Anything else we should know?"
              value={intakeNotes}
              onChange={(e) => setIntakeNotes(e.target.value)}
              placeholder="Allergies, medical conditions, lifestyle..."
              rows={3}
            />
            <Button type="submit" isLoading={intakeSubmitting}>
              Submit — Get Started
            </Button>
          </form>
        </div>
      </section>

      {articles.length > 0 && (
        <section className="landing__articles">
          <div className="landing__articles-inner">
            <h2 className="landing__section-title">Articles</h2>
            <div className="landing__articles-grid">
              {articles.map((article) => (
                <Link
                  key={article.id}
                  to={`/p/${slug}/${article.slug}`}
                  className="landing__article-card"
                >
                  {article.cover_image_url && (
                    <img
                      src={article.cover_image_url}
                      alt={article.title}
                      className="landing__article-cover"
                    />
                  )}
                  <div className="landing__article-body">
                    <h3 className="landing__article-title">{article.title}</h3>
                    {article.summary && (
                      <p className="landing__article-summary">{article.summary}</p>
                    )}
                    <div className="landing__article-meta">
                      <span>{formatDate(article.published_at)}</span>
                      {article.tags && article.tags.length > 0 && (
                        <div className="landing__article-tags">
                          {article.tags.slice(0, 3).map((tag) => (
                            <span key={tag} className="landing__article-tag">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      <footer className="landing__footer">
        <div className="landing__footer-inner">
          <p>
            Powered by{' '}
            <a href="/" className="landing__footer-link">
              NutriPlan
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
