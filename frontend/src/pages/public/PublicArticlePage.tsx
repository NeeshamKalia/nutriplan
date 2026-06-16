import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { publicApi, type DietitianPublicProfile, type Article } from '../../api/articles';
import './PublicPages.css';

export function PublicArticlePage() {
  const { slug, articleSlug } = useParams<{ slug: string; articleSlug: string }>();
  const [dietitian, setDietitian] = useState<DietitianPublicProfile | null>(null);
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!slug || !articleSlug) return;
    const fetchData = async () => {
      try {
        const [profile, art] = await Promise.all([
          publicApi.getDietitian(slug),
          publicApi.getArticle(slug, articleSlug),
        ]);
        setDietitian(profile);
        setArticle(art);
      } catch {
        setError('Article not found.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [slug, articleSlug]);

  if (loading) {
    return (
      <div className="public-page__loading">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !article || !dietitian) {
    return (
      <div className="public-page__error">
        <h1>Not Found</h1>
        <p>{error || 'This article does not exist.'}</p>
        {slug && (
          <Link to={`/p/${slug}`} className="public-page__back-link">
            &larr; Back to profile
          </Link>
        )}
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

  const renderContent = (raw: string) => {
    const isHtml = /<[a-z][\s\S]*>/i.test(raw);
    if (isHtml) {
      return (
        <div
          className="article-view__content article-view__content--html"
          dangerouslySetInnerHTML={{ __html: raw }}
        />
      );
    }
    return (
      <div className="article-view__content">
        {raw.split('\n').map((paragraph, i) => {
          if (!paragraph.trim()) return <br key={i} />;
          if (paragraph.startsWith('# ')) {
            return <h1 key={i} className="article-content__h1">{paragraph.slice(2)}</h1>;
          }
          if (paragraph.startsWith('## ')) {
            return <h2 key={i} className="article-content__h2">{paragraph.slice(3)}</h2>;
          }
          if (paragraph.startsWith('### ')) {
            return <h3 key={i} className="article-content__h3">{paragraph.slice(4)}</h3>;
          }
          if (paragraph.startsWith('- ') || paragraph.startsWith('* ')) {
            return <li key={i} className="article-content__li">{paragraph.slice(2)}</li>;
          }
          return <p key={i} className="article-content__p">{paragraph}</p>;
        })}
      </div>
    );
  };

  const seoTitle = article.meta_title || article.title;
  const seoDescription = article.meta_description || article.summary || `${article.title} by ${dietitian.full_name}`;

  return (
    <div className="public-page">
      <Helmet>
        <title>{seoTitle} | {dietitian.full_name} — NutriPlan</title>
        <meta name="description" content={seoDescription} />
        <meta property="og:title" content={seoTitle} />
        <meta property="og:description" content={seoDescription} />
        <meta property="og:type" content="article" />
        <meta property="article:author" content={dietitian.full_name} />
        {article.published_at && (
          <meta property="article:published_time" content={article.published_at} />
        )}
        {article.cover_image_url && (
          <meta property="og:image" content={article.cover_image_url} />
        )}
        {article.tags?.map((tag) => (
          <meta key={tag} property="article:tag" content={tag} />
        ))}
      </Helmet>

      <header className="landing__header">
        <div className="landing__header-inner">
          <Link to={`/p/${slug}`} className="landing__brand">
            <span className="landing__brand-name">NutriPlan</span>
          </Link>
        </div>
      </header>

      <article className="article-view">
        <div className="article-view__inner">
          <Link to={`/p/${slug}`} className="article-view__back">
            &larr; Back to {dietitian.full_name}
          </Link>

          {article.cover_image_url && (
            <img
              src={article.cover_image_url}
              alt={article.title}
              className="article-view__cover"
            />
          )}

          <h1 className="article-view__title">{article.title}</h1>

          <div className="article-view__meta">
            <span className="article-view__author">By {dietitian.full_name}</span>
            {article.published_at && (
              <span className="article-view__date">
                {formatDate(article.published_at)}
              </span>
            )}
          </div>

          {article.tags && article.tags.length > 0 && (
            <div className="article-view__tags">
              {article.tags.map((tag) => (
                <span key={tag} className="landing__article-tag">
                  {tag}
                </span>
              ))}
            </div>
          )}

          {renderContent(article.content)}
        </div>
      </article>

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
