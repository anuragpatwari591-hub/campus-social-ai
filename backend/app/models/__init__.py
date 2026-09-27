"""
Import every model module here so that Base.metadata.create_all() (used in
app.main on startup, and in tests) discovers all tables regardless of which
module happens to be imported first.
"""
from app.models.geo import Country, Region, City, Institution, InstitutionAlias, Campus
from app.models.user import User, AnonymousProfile, UserInterest, Block, Notification
from app.models.content import (
    Post,
    PostMedia,
    Comment,
    Reaction,
    Poll,
    PollOption,
    PollVote,
    Reel,
    Story,
    StoryView,
)
from app.models.social import (
    Community,
    CommunityMember,
    Room,
    RoomMember,
    RoomMessage,
    Match,
    Connection,
    Conversation,
    ConversationParticipant,
    Message,
)
from app.models.moderation import Report, ModerationAction, IdentityAccessLog
from app.models.ai import AIRequest, AIFeedback, RecommendationWeight
from app.models.campus_life import Event, EventRegistration, Opportunity, MarketplaceListing
from app.models.monetization import Sponsor, Campaign

__all__ = [
    "Country", "Region", "City", "Institution", "InstitutionAlias", "Campus",
    "User", "AnonymousProfile", "UserInterest", "Block", "Notification",
    "Post", "PostMedia", "Comment", "Reaction", "Poll", "PollOption", "PollVote",
    "Reel", "Story", "StoryView",
    "Community", "CommunityMember", "Room", "RoomMember", "RoomMessage",
    "Match", "Connection", "Conversation", "ConversationParticipant", "Message",
    "Report", "ModerationAction", "IdentityAccessLog",
    "AIRequest", "AIFeedback", "RecommendationWeight",
    "Event", "EventRegistration", "Opportunity", "MarketplaceListing",
    "Sponsor", "Campaign",
]
