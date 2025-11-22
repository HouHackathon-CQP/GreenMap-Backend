import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    CITIZEN = "CITIZEN"


class LocationType(str, enum.Enum):
    CHARGING_STATION = "CHARGING_STATION"
    GREEN_SPACE = "GREEN_SPACE"
    PUBLIC_PARK = "PUBLIC_PARK"
    BICYCLE_RENTAL = "BICYCLE_RENTAL"
    TOURIST_ATTRACTION = "TOURIST_ATTRACTION"


class ReportStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
