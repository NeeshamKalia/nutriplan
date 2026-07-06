import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input, Textarea } from '../../components/ui/Input';
import { RichTextEditor } from '../../components/ui/RichTextEditor';
import { Badge } from '../../components/ui/Badge';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { ConfirmModal } from '../../components/ui/ConfirmModal';
import { articlesApi, type Article, type ArticleCreatePayload } from '../../api/articles';
import './ArticleEditorPage.css';

export function ArticleEditorPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditing = !!id;

  const [loading, setLoading] = useState(isEditing);
  const [saving, setSaving] = useState(false);
  const [broadcasting, setBroadcasting] = useState(false);
  const [article, setArticle] = useState<Article | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showBroadcastConfirm, setShowBroadcastConfirm] = useState(false);

  const [title, setTitle] = useState('');
  const [slug, setSlug] = useState('');
  const [summary, setSummary] = useState('');
  const [content, setContent] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [metaTitle, setMetaTitle] = useState('');
  const [metaDescription, setMetaDescription] = useState('');
  const [coverImageUrl, setCoverImageUrl] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (!isEditing) return;
    const fetchArticle = async () => {
      try {
        const data = await articlesApi.get(id);
        setArticle(data);
        setTitle(data.title);
        setSlug(data.slug);
        setSummary(data.summary || '');
        setContent(data.content);
        setTagsInput(data.tags?.join(', ') || '');
        setMetaTitle(data.meta_title || '');
        setMetaDescription(data.meta_description || '');
        setCoverImageUrl(data.cover_image_url || '');
      } catch {
        setError('Article not found.');
      } finally {
        setLoading(false);
      }
    };
    fetchArticle();
  }, [id, isEditing]);

  const parseTags = useCallback((): string[] => {
    return tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter(Boolean);
  }, [tagsInput]);

  const handleSave = async (publish = false) => {
    const textContent = content.replace(/<[^>]+>/g, '').trim();
    if (!title.trim() || !textContent) {
      setError('Title and content are required.');
      return;
    }
    setError('');
    setSaving(true);

    try {
      const payload: ArticleCreatePayload = {
        title: title.trim(),
        content: content.trim(),
        summary: summary.trim() || undefined,
        slug: slug.trim() || undefined,
        tags: parseTags().length > 0 ? parseTags() : undefined,
        meta_title: metaTitle.trim() || undefined,
        meta_description: metaDescription.trim() || undefined,
        cover_image_url: coverImageUrl.trim() || undefined,
        status: publish ? 'published' : 'draft',
      };

      if (isEditing) {
        const updated = await articlesApi.update(id, payload);
        if (publish && updated.status !== 'published') {
          await articlesApi.publish(id);
        }
        setArticle(updated);
      } else {
        const created = await articlesApi.create(payload);
        navigate(`/articles/${created.id}/edit`, { replace: true });
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save article.');
    } finally {
      setSaving(false);
    }
  };

  const handlePublishToggle = async () => {
    if (!article) return;
    setSaving(true);
    try {
      if (article.status === 'published') {
        const updated = await articlesApi.unpublish(article.id);
        setArticle(updated);
      } else {
        const updated = await articlesApi.publish(article.id);
        setArticle(updated);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update status.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!article) return;
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirmed = async () => {
    if (!article) return;
    setShowDeleteConfirm(false);
    try {
      await articlesApi.delete(article.id);
      navigate('/articles');
    } catch {
      setError('Failed to delete article.');
    }
  };

  const handleBroadcast = async () => {
    if (!article || article.status !== 'published') return;
    setShowBroadcastConfirm(true);
  };

  const handleBroadcastConfirmed = async () => {
    if (!article) return;
    setShowBroadcastConfirm(false);
    setBroadcasting(true);
    setError('');
    try {
      const result = await articlesApi.broadcast(article.id);
      setArticle(result.article);
    } catch (err: unknown) {
      const message =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data
              ?.detail
          : undefined;
      setError(message || 'Failed to broadcast article.');
    } finally {
      setBroadcasting(false);
    }
  };

  if (loading) {
    return (
      <div className="article-editor__loading">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="article-editor">
      <div className="article-editor__header">
        <div className="article-editor__header-left">
          <button
            className="article-editor__back"
            onClick={() => navigate('/articles')}
          >
            &larr; Articles
          </button>
          <h1 className="article-editor__title">
            {isEditing ? 'Edit Article' : 'New Article'}
          </h1>
          {article && (
            <Badge variant={article.status === 'published' ? 'success' : 'default'}>
              {article.status}
            </Badge>
          )}
        </div>
        <div className="article-editor__header-actions">
          {isEditing && article && (
            <>
              {article.status === 'published' && (
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleBroadcast}
                  isLoading={broadcasting}
                  disabled={saving}
                >
                  Broadcast to Clients
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={handlePublishToggle} disabled={saving}>
                {article.status === 'published' ? 'Unpublish' : 'Publish'}
              </Button>
              <Button variant="danger" size="sm" onClick={handleDelete}>
                Delete
              </Button>
            </>
          )}
          <Button
            variant="secondary"
            onClick={() => handleSave(false)}
            isLoading={saving}
          >
            Save Draft
          </Button>
          <Button onClick={() => handleSave(true)} isLoading={saving}>
            Save & Publish
          </Button>
        </div>
      </div>

      {error && <div className="article-editor__error">{error}</div>}

      <div className="article-editor__body">
        <div className="article-editor__main">
          <Card>
            <Input
              label="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. 10 Indian Superfoods for Weight Loss"
            />
            <div style={{ marginTop: 'var(--space-4)' }}>
              <Textarea
                label="Summary"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
                placeholder="Brief description shown in article cards and SEO..."
                rows={2}
              />
            </div>
            <div style={{ marginTop: 'var(--space-4)' }}>
              <RichTextEditor
                label="Content"
                value={content}
                onChange={setContent}
                placeholder="Write your article content here..."
              />
            </div>
          </Card>
        </div>

        <div className="article-editor__sidebar">
          <Card>
            <h3 className="article-editor__sidebar-title">Settings</h3>

            <div className="article-editor__field">
              <Input
                label="URL Slug"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="Auto-generated from title"
                hint="Leave blank for auto-generation"
              />
            </div>

            <div className="article-editor__field">
              <Input
                label="Tags"
                value={tagsInput}
                onChange={(e) => setTagsInput(e.target.value)}
                placeholder="nutrition, wellness, tips"
                hint="Comma-separated"
              />
            </div>

            <div className="article-editor__field">
              <Input
                label="Cover Image URL"
                value={coverImageUrl}
                onChange={(e) => setCoverImageUrl(e.target.value)}
                placeholder="https://..."
              />
            </div>
          </Card>

          <Card>
            <h3 className="article-editor__sidebar-title">SEO</h3>

            <div className="article-editor__field">
              <Input
                label="Meta Title"
                value={metaTitle}
                onChange={(e) => setMetaTitle(e.target.value)}
                placeholder="Custom page title for search engines"
                hint={`${metaTitle.length}/60 characters`}
              />
            </div>

            <div className="article-editor__field">
              <Textarea
                label="Meta Description"
                value={metaDescription}
                onChange={(e) => setMetaDescription(e.target.value)}
                placeholder="Brief description for search engine results..."
                rows={3}
              />
              <p className="text-xs text-muted" style={{ marginTop: '0.25rem' }}>
                {metaDescription.length}/160 characters
              </p>
            </div>
          </Card>

          {article?.published_at && (
            <Card>
              <h3 className="article-editor__sidebar-title">Info</h3>
              <div className="article-editor__info-row">
                <span className="text-muted">Published</span>
                <span>
                  {new Date(article.published_at).toLocaleDateString('en-IN', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  })}
                </span>
              </div>
              {article.broadcasted_at && (
                <div className="article-editor__info-row">
                  <span className="text-muted">Last broadcast</span>
                  <span>
                    {new Date(article.broadcasted_at).toLocaleDateString('en-IN', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })}{' '}
                    ({article.broadcast_count} sent)
                  </span>
                </div>
              )}
              <div className="article-editor__info-row">
                <span className="text-muted">Created</span>
                <span>
                  {new Date(article.created_at).toLocaleDateString('en-IN', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                  })}
                </span>
              </div>
            </Card>
          )}
        </div>
      </div>

      <ConfirmModal
        isOpen={showDeleteConfirm}
        title="Delete Article"
        message="Delete this article permanently? This cannot be undone."
        confirmLabel="Delete"
        variant="danger"
        onConfirm={handleDeleteConfirmed}
        onCancel={() => setShowDeleteConfirm(false)}
      />

      <ConfirmModal
        isOpen={showBroadcastConfirm}
        title="Broadcast Article"
        message={`Send "${article?.title}" to all active clients via WhatsApp?`}
        confirmLabel="Send Broadcast"
        variant="primary"
        onConfirm={handleBroadcastConfirmed}
        onCancel={() => setShowBroadcastConfirm(false)}
      />
    </div>
  );
}
