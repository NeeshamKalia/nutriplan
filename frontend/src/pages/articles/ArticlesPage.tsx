import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Input } from '../../components/ui/Input';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { articlesApi, type Article } from '../../api/articles';
import { EmptyState } from '../../components/ui/EmptyState';
import './ArticlesPage.css';

export function ArticlesPage() {
  const navigate = useNavigate();
  const [articles, setArticles] = useState<Article[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (search) params.search = search;
      if (statusFilter) params.status = statusFilter;
      const data = await articlesApi.list(params);
      setArticles(data.articles);
      setTotal(data.total);
    } catch (err) {
      console.error('Failed to load articles', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArticles();
  }, [statusFilter]);

  useEffect(() => {
    const timer = setTimeout(fetchArticles, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this article?')) return;
    try {
      await articlesApi.delete(id);
      fetchArticles();
    } catch (err) {
      console.error('Failed to delete article', err);
    }
  };

  const handleTogglePublish = async (article: Article) => {
    try {
      if (article.status === 'published') {
        await articlesApi.unpublish(article.id);
      } else {
        await articlesApi.publish(article.id);
      }
      fetchArticles();
    } catch (err) {
      console.error('Failed to toggle publish', err);
    }
  };

  const handleBroadcast = async (article: Article) => {
    if (article.status !== 'published') {
      window.alert('Publish the article before broadcasting to clients.');
      return;
    }
    if (
      !window.confirm(
        `Send "${article.title}" to all active clients via WhatsApp?`
      )
    ) {
      return;
    }
    try {
      const result = await articlesApi.broadcast(article.id);
      window.alert(
        `Broadcast sent to ${result.sent_count} client${result.sent_count !== 1 ? 's' : ''}.` +
          (result.skipped_count > 0
            ? ` ${result.skipped_count} skipped (no WhatsApp number).`
            : '') +
          (result.failed_count > 0 ? ` ${result.failed_count} failed.` : '')
      );
      fetchArticles();
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data
              ?.detail
          : undefined;
      window.alert(message || 'Failed to broadcast article.');
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  return (
    <div className="articles-page">
      <div className="articles-page__header">
        <div>
          <h1 className="articles-page__title">Articles</h1>
          <p className="text-muted">Write and publish articles for your landing page.</p>
        </div>
        <Button onClick={() => navigate('/articles/new')}>New Article</Button>
      </div>

      <div className="articles-page__filters">
        <div className="articles-page__search">
          <Input
            placeholder="Search articles..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          className="articles-page__status-select"
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">All Status</option>
          <option value="draft">Drafts</option>
          <option value="published">Published</option>
        </select>
      </div>

      {loading ? (
        <div className="articles-page__loading">
          <LoadingSpinner />
        </div>
      ) : articles.length === 0 ? (
        <Card>
          <EmptyState
            icon="✍️"
            title={search || statusFilter ? 'No matching articles' : 'No articles yet'}
            description={
              search || statusFilter
                ? 'Try adjusting your search or filter to find what you\'re looking for.'
                : 'Write your first article to share nutrition tips with your clients and boost your landing page SEO.'
            }
            actionLabel={!search && !statusFilter ? 'Write Your First Article' : undefined}
            onAction={!search && !statusFilter ? () => navigate('/articles/new') : undefined}
          />
        </Card>
      ) : (
        <div className="articles-page__list">
          <div className="articles-page__count text-muted text-sm">
            {total} article{total !== 1 ? 's' : ''}
          </div>
          {articles.map((article) => (
            <Card key={article.id} hover className="articles-page__card">
              <div
                className="articles-page__card-content"
                onClick={() => navigate(`/articles/${article.id}/edit`)}
              >
                <div className="articles-page__card-main">
                  <div className="articles-page__card-top">
                    <h3 className="articles-page__card-title">{article.title}</h3>
                    <Badge
                      variant={article.status === 'published' ? 'success' : 'default'}
                    >
                      {article.status}
                    </Badge>
                  </div>
                  {article.summary && (
                    <p className="articles-page__card-summary text-muted">
                      {article.summary}
                    </p>
                  )}
                  <div className="articles-page__card-meta text-sm text-muted">
                    <span>Created {formatDate(article.created_at)}</span>
                    {article.published_at && (
                      <span>Published {formatDate(article.published_at)}</span>
                    )}
                    {article.broadcasted_at && (
                      <span>
                        Broadcast {formatDate(article.broadcasted_at)} (
                        {article.broadcast_count} sent)
                      </span>
                    )}
                    {article.tags && article.tags.length > 0 && (
                      <span className="articles-page__card-tags">
                        {article.tags.map((tag) => (
                          <span key={tag} className="articles-page__tag">
                            {tag}
                          </span>
                        ))}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              <div className="articles-page__card-actions">
                {article.status === 'published' && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleBroadcast(article);
                    }}
                  >
                    Broadcast
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleTogglePublish(article);
                  }}
                >
                  {article.status === 'published' ? 'Unpublish' : 'Publish'}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    navigate(`/articles/${article.id}/edit`);
                  }}
                >
                  Edit
                </Button>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(article.id);
                  }}
                >
                  Delete
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
