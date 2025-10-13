"""
Pydantic Schemas

All request/response schemas for API endpoints.
"""
from backend.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    UserResponse,
    UserUpdate,
    PasswordChange,
    PasswordResetRequest,
    PasswordReset,
    EmailVerificationRequest,
    EmailVerificationResend,
    AuthStatus,
)
from backend.schemas.agent_message import (
    AgentMessageBase,
    AgentMessageCreate,
    AgentMessageResponse,
    MessageStats,
    TaskAssignment,
    StatusRequest,
    StatusUpdate,
    Question,
    Answer,
    HumanInterventionRequired,
    CodeReviewRequest,
    CodeReviewResponse,
    TaskCompletion,
    Standup,
    MessagePayload,
)
from backend.schemas.squad import (
    SquadBase,
    SquadCreate,
    SquadUpdate,
    SquadResponse,
    SquadMemberSummary,
    SquadWithAgents,
    SquadCostEstimate,
)
from backend.schemas.squad_member import (
    SquadMemberBase,
    SquadMemberCreate,
    SquadMemberUpdate,
    SquadMemberResponse,
    SquadMemberWithConfig,
    SquadComposition,
)
from backend.schemas.task_execution import (
    TaskExecutionBase,
    TaskExecutionCreate,
    TaskExecutionResponse,
    TaskExecutionWithMessages,
    TaskExecutionSummary,
    TaskExecutionCancel,
    HumanIntervention,
)

__all__ = [
    # Auth schemas
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "TokenRefresh",
    "UserResponse",
    "UserUpdate",
    "PasswordChange",
    "PasswordResetRequest",
    "PasswordReset",
    "EmailVerificationRequest",
    "EmailVerificationResend",
    "AuthStatus",
    # Agent message schemas
    "AgentMessageBase",
    "AgentMessageCreate",
    "AgentMessageResponse",
    "MessageStats",
    "TaskAssignment",
    "StatusRequest",
    "StatusUpdate",
    "Question",
    "Answer",
    "HumanInterventionRequired",
    "CodeReviewRequest",
    "CodeReviewResponse",
    "TaskCompletion",
    "Standup",
    "MessagePayload",
    # Squad schemas
    "SquadBase",
    "SquadCreate",
    "SquadUpdate",
    "SquadResponse",
    "SquadMemberSummary",
    "SquadWithAgents",
    "SquadCostEstimate",
    # Squad member schemas
    "SquadMemberBase",
    "SquadMemberCreate",
    "SquadMemberUpdate",
    "SquadMemberResponse",
    "SquadMemberWithConfig",
    "SquadComposition",
    # Task execution schemas
    "TaskExecutionBase",
    "TaskExecutionCreate",
    "TaskExecutionResponse",
    "TaskExecutionWithMessages",
    "TaskExecutionSummary",
    "TaskExecutionCancel",
    "HumanIntervention",
]
