import enum


class VacancyStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    ARCHIVED = "archived"


class ReactionAction(str, enum.Enum):
    LIKE = "like"
    DISLIKE = "dislike"


class ReactionSource(str, enum.Enum):
    TELEGRAM_BOT = "telegram_bot"
    WEB = "web"


class EntityType(str, enum.Enum):
    CANDIDATE = "candidate"
    ORGANIZATION = "organization"


class MatchStatus(str, enum.Enum):
    PENDING_RESPONSE = "pending_response"
    MUTUAL_MATCHED = "mutual_matched"
    NOTIFIED = "notified"
    CLOSED = "closed"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class ProfileChangeSource(str, enum.Enum):
    TELEGRAM_BOT = "telegram_bot"
    WEB = "web"
    SYSTEM = "system"


class MatchConfidence(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
