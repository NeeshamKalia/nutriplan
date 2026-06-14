"""SQLAlchemy models — import all models here so Alembic can detect them."""

from app.models.dietitian import Dietitian
from app.models.refresh_token import RefreshToken
from app.models.client import Client
from app.models.meal_plan import MealPlan, MealPlanDay, MealPlanItem, MealPlanValidation
from app.models.meal_log import MealLog
from app.models.progress_log import ProgressLog
from app.models.whatsapp_message import WhatsAppMessage
from app.models.protocol import Protocol
from app.models.article import Article, ArticleEmbedding
from app.models.food_item import FoodItem
from app.models.audit_log import AuditLog

__all__ = [
    "Dietitian",
    "RefreshToken",
    "Client",
    "MealPlan",
    "MealPlanDay",
    "MealPlanItem",
    "MealPlanValidation",
    "MealLog",
    "ProgressLog",
    "WhatsAppMessage",
    "Protocol",
    "Article",
    "ArticleEmbedding",
    "FoodItem",
    "AuditLog",
]
