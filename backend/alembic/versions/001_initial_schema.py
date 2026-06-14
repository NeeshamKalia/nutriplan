"""Initial schema — all NutriPlan tables.

Revision ID: 001
Revises:
Create Date: 2026-06-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')

    # --- DIETITIANS ---
    op.create_table(
        "dietitians",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("photo_url", sa.Text()),
        sa.Column("bio", sa.Text()),
        sa.Column("specializations", postgresql.ARRAY(sa.Text())),
        sa.Column("qualifications", sa.Text()),
        sa.Column("practice_name", sa.String(255)),
        sa.Column("whatsapp_phone_number_id", sa.String(50)),
        sa.Column("whatsapp_business_account_id", sa.String(50)),
        sa.Column("whatsapp_access_token", sa.Text()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- REFRESH TOKENS ---
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("dietitian_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dietitians.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("replaced_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("refresh_tokens.id")),
        sa.Column("user_agent", sa.Text()),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_refresh_tokens_dietitian", "refresh_tokens", ["dietitian_id"])
    op.create_index("idx_refresh_tokens_hash", "refresh_tokens", ["token_hash"])

    # --- PROTOCOLS (before meal_plans due to FK) ---
    op.create_table(
        "protocols",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("dietitian_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dietitians.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("target_conditions", postgresql.ARRAY(sa.Text())),
        sa.Column("target_goals", postgresql.ARRAY(sa.Text())),
        sa.Column("calorie_range_min", sa.Integer()),
        sa.Column("calorie_range_max", sa.Integer()),
        sa.Column("macro_split", postgresql.JSONB()),
        sa.Column("general_guidelines", sa.Text()),
        sa.Column("preferred_foods", postgresql.ARRAY(sa.Text())),
        sa.Column("avoided_foods", postgresql.ARRAY(sa.Text())),
        sa.Column("sample_plan", postgresql.JSONB()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- CLIENTS ---
    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("dietitian_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dietitians.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("whatsapp_number", sa.String(20), nullable=False),
        sa.Column("email", sa.String(255)),
        sa.Column("age", sa.Integer()),
        sa.Column("gender", sa.String(20)),
        sa.Column("height_cm", sa.Numeric(5, 1)),
        sa.Column("weight_kg", sa.Numeric(5, 1)),
        sa.Column("target_weight_kg", sa.Numeric(5, 1)),
        sa.Column("activity_level", sa.String(50)),
        sa.Column("medical_conditions", postgresql.ARRAY(sa.Text())),
        sa.Column("allergies", postgresql.ARRAY(sa.Text())),
        sa.Column("food_preferences", postgresql.ARRAY(sa.Text())),
        sa.Column("cuisine_preference", sa.String(50)),
        sa.Column("dietary_type", sa.String(50)),
        sa.Column("primary_goal", sa.String(100)),
        sa.Column("monthly_food_budget_inr", sa.Integer()),
        sa.Column("daily_calorie_target", sa.Integer()),
        sa.Column("meals_per_day", sa.Integer(), server_default=sa.text("5")),
        sa.Column("meal_timing_preferences", postgresql.JSONB()),
        sa.Column("notes", sa.Text()),
        sa.Column("lifestyle_notes", sa.Text()),
        sa.Column("status", sa.String(20), server_default=sa.text("'active'")),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        sa.Column("onboarded_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("dietitian_id", "whatsapp_number", name="uq_client_whatsapp"),
    )
    op.create_index("idx_clients_dietitian", "clients", ["dietitian_id"])
    op.create_index("idx_clients_whatsapp", "clients", ["whatsapp_number"])

    # --- FOOD ITEMS (before meal_plan_items due to FK) ---
    op.create_table(
        "food_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("dietitian_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dietitians.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_hindi", sa.String(255)),
        sa.Column("category", sa.String(100)),
        sa.Column("subcategory", sa.String(100)),
        sa.Column("calories_per_100g", sa.Integer()),
        sa.Column("protein_per_100g", sa.Numeric(5, 1)),
        sa.Column("carbs_per_100g", sa.Numeric(5, 1)),
        sa.Column("fat_per_100g", sa.Numeric(5, 1)),
        sa.Column("fiber_per_100g", sa.Numeric(5, 1)),
        sa.Column("default_serving_description", sa.String(100)),
        sa.Column("default_serving_grams", sa.Numeric(6, 1)),
        sa.Column("is_vegetarian", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("is_vegan", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("is_gluten_free", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("common_allergens", postgresql.ARRAY(sa.Text())),
        sa.Column("approx_cost_per_kg_inr", sa.Integer()),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_food_items_category", "food_items", ["category"])
    op.create_index("idx_food_items_dietitian", "food_items", ["dietitian_id"])

    # --- MEAL PLANS ---
    op.create_table(
        "meal_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("dietitian_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dietitians.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("week_start_date", sa.Date()),
        sa.Column("status", sa.String(20), server_default=sa.text("'draft'")),
        sa.Column("generation_prompt", sa.Text()),
        sa.Column("generation_model", sa.String(100)),
        sa.Column("generation_tokens_used", sa.Integer()),
        sa.Column("generation_cost_usd", sa.Numeric(10, 6)),
        sa.Column("generation_duration_ms", sa.Integer()),
        sa.Column("custom_instructions", sa.Text()),
        sa.Column("avg_daily_calories", sa.Integer()),
        sa.Column("avg_daily_protein_g", sa.Numeric(5, 1)),
        sa.Column("avg_daily_carbs_g", sa.Numeric(5, 1)),
        sa.Column("avg_daily_fat_g", sa.Numeric(5, 1)),
        sa.Column("avg_daily_fiber_g", sa.Numeric(5, 1)),
        sa.Column("protocol_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("protocols.id"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_meal_plans_client", "meal_plans", ["client_id"])
    op.create_index("idx_meal_plans_dietitian", "meal_plans", ["dietitian_id"])

    # --- MEAL PLAN DAYS ---
    op.create_table(
        "meal_plan_days",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("meal_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.Column("day_label", sa.String(20)),
        sa.Column("total_calories", sa.Integer()),
        sa.Column("total_protein_g", sa.Numeric(5, 1)),
        sa.Column("total_carbs_g", sa.Numeric(5, 1)),
        sa.Column("total_fat_g", sa.Numeric(5, 1)),
        sa.Column("total_fiber_g", sa.Numeric(5, 1)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_meal_plan_days_plan", "meal_plan_days", ["meal_plan_id"])

    # --- MEAL PLAN ITEMS ---
    op.create_table(
        "meal_plan_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("meal_plan_day_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("meal_plan_days.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meal_type", sa.String(30), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0")),
        sa.Column("food_name", sa.String(255), nullable=False),
        sa.Column("food_name_hindi", sa.String(255)),
        sa.Column("portion_description", sa.String(255)),
        sa.Column("portion_grams", sa.Numeric(6, 1)),
        sa.Column("calories", sa.Integer()),
        sa.Column("protein_g", sa.Numeric(5, 1)),
        sa.Column("carbs_g", sa.Numeric(5, 1)),
        sa.Column("fat_g", sa.Numeric(5, 1)),
        sa.Column("fiber_g", sa.Numeric(5, 1)),
        sa.Column("food_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("food_items.id"), nullable=True),
        sa.Column("preparation_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_meal_plan_items_day", "meal_plan_items", ["meal_plan_day_id"])

    # --- MEAL PLAN VALIDATIONS ---
    op.create_table(
        "meal_plan_validations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("meal_plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("validation_type", sa.String(50), nullable=False),
        sa.Column("passed", sa.Boolean(), nullable=False),
        sa.Column("severity", sa.String(20)),
        sa.Column("message", sa.Text()),
        sa.Column("details", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # --- MEAL LOGS ---
    op.create_table(
        "meal_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("meal_plan_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("meal_plan_items.id"), nullable=True),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("meal_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("deviation_note", sa.Text()),
        sa.Column("logged_via", sa.String(20), server_default=sa.text("'whatsapp'")),
        sa.Column("logged_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_meal_logs_client_date", "meal_logs", ["client_id", "log_date"])

    # --- PROGRESS LOGS ---
    op.create_table(
        "progress_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("weight_kg", sa.Numeric(5, 1)),
        sa.Column("waist_cm", sa.Numeric(5, 1)),
        sa.Column("hip_cm", sa.Numeric(5, 1)),
        sa.Column("chest_cm", sa.Numeric(5, 1)),
        sa.Column("notes", sa.Text()),
        sa.Column("logged_via", sa.String(20), server_default=sa.text("'dashboard'")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("client_id", "log_date", name="uq_progress_client_date"),
    )
    op.create_index("idx_progress_logs_client", "progress_logs", ["client_id", "log_date"])

    # --- WHATSAPP MESSAGES ---
    op.create_table(
        "whatsapp_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id"), nullable=True),
        sa.Column("dietitian_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dietitians.id"), nullable=True),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("wa_message_id", sa.String(255)),
        sa.Column("from_number", sa.String(20)),
        sa.Column("to_number", sa.String(20)),
        sa.Column("message_type", sa.String(20)),
        sa.Column("message_body", sa.Text()),
        sa.Column("template_name", sa.String(100)),
        sa.Column("status", sa.String(20)),
        sa.Column("error_message", sa.Text()),
        sa.Column("intent", sa.String(50)),
        sa.Column("ai_response", sa.Text()),
        sa.Column("ai_model", sa.String(100)),
        sa.Column("ai_tokens_used", sa.Integer()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_wa_messages_client", "whatsapp_messages", ["client_id"])
    op.create_index("idx_wa_messages_direction", "whatsapp_messages", ["direction", "created_at"])

    # --- ARTICLES ---
    op.create_table(
        "articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("dietitian_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dietitians.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("cover_image_url", sa.Text()),
        sa.Column("tags", postgresql.ARRAY(sa.Text())),
        sa.Column("status", sa.String(20), server_default=sa.text("'draft'")),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("meta_title", sa.String(200)),
        sa.Column("meta_description", sa.String(300)),
        sa.Column("broadcasted_at", sa.DateTime(timezone=True)),
        sa.Column("broadcast_count", sa.Integer(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("dietitian_id", "slug", name="uq_article_slug"),
    )
    op.create_index("idx_articles_dietitian", "articles", ["dietitian_id"])
    op.create_index("idx_articles_status", "articles", ["status", "published_at"])

    # --- ARTICLE EMBEDDINGS ---
    op.create_table(
        "article_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("articles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    # Add vector column via raw SQL (pgvector)
    op.execute("ALTER TABLE article_embeddings ADD COLUMN embedding vector(768)")
    op.execute("CREATE INDEX idx_article_embeddings_vector ON article_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")

    # --- AUDIT LOGS ---
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("dietitian_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dietitians.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True)),
        sa.Column("metadata", postgresql.JSONB()),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_audit_logs_dietitian", "audit_logs", ["dietitian_id"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action", "created_at"])
    op.create_index("idx_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("article_embeddings")
    op.drop_table("articles")
    op.drop_table("whatsapp_messages")
    op.drop_table("progress_logs")
    op.drop_table("meal_logs")
    op.drop_table("meal_plan_validations")
    op.drop_table("meal_plan_items")
    op.drop_table("meal_plan_days")
    op.drop_table("meal_plans")
    op.drop_table("food_items")
    op.drop_table("clients")
    op.drop_table("protocols")
    op.drop_table("refresh_tokens")
    op.drop_table("dietitians")
    op.execute('DROP EXTENSION IF EXISTS "vector"')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
