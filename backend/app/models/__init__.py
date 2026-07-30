# Import all models so SQLAlchemy creates all tables via Base.metadata.create_all()
from app.models.user import User
from app.models.health_profile import HealthProfile
from app.models.medical import MedicalCondition, InjuryRecord, Contraindication
from app.models.workout import WeeklyPlan, WorkoutSession, FavouriteExercise
from app.models.nutrition import NutritionLog, NutritionPlan
from app.models.progress import ProgressMetric, SleepLog, HydrationLog
from app.models.chat import AIConversation, ChatSession
from app.models.memory import UserMemory, UserSemanticMemory
from app.models.evaluation import FeedbackEvent, Experiment, ExperimentAssignment, EvaluationMetric
from app.models.review import Review
from app.models.audit import AuditLog
