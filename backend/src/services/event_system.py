"""
Event and notification system for music app.

Features:
- Event publishing and subscription
- Real-time notifications
- Activity logging
- Webhook support
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from collections import defaultdict
import threading
import queue
import json
import logging

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    # User events
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    
    # Song events
    SONG_PLAYED = "song.played"
    SONG_LIKED = "song.liked"
    SONG_DISLIKED = "song.disliked"
    SONG_SKIPPED = "song.skipped"
    SONG_COMPLETED = "song.completed"
    SONG_ADDED = "song.added"
    SONG_UPDATED = "song.updated"
    
    # Playlist events
    PLAYLIST_CREATED = "playlist.created"
    PLAYLIST_UPDATED = "playlist.updated"
    PLAYLIST_DELETED = "playlist.deleted"
    PLAYLIST_SONG_ADDED = "playlist.song_added"
    PLAYLIST_SONG_REMOVED = "playlist.song_removed"
    PLAYLIST_FOLLOWED = "playlist.followed"
    
    # Recommendation events
    RECOMMENDATION_GENERATED = "recommendation.generated"
    MOOD_PREDICTED = "mood.predicted"
    
    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    BACKUP_CREATED = "backup.created"
    EXPORT_COMPLETED = "export.completed"


@dataclass
class Event:
    """Represents an event in the system."""
    event_type: EventType
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    source: str = "api"
    
    def to_dict(self) -> Dict:
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "source": self.source
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict())


class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Notification:
    """User notification."""
    user_id: int
    title: str
    message: str
    notification_type: NotificationType = NotificationType.INFO
    timestamp: datetime = field(default_factory=datetime.now)
    read: bool = False
    action_url: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "type": self.notification_type.value,
            "timestamp": self.timestamp.isoformat(),
            "read": self.read,
            "action_url": self.action_url,
            "data": self.data
        }


EventHandler = Callable[[Event], None]


class EventBus:
    """
    Central event bus for publish-subscribe pattern.
    
    Thread-safe implementation with async event processing.
    """
    
    _instance: Optional["EventBus"] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self._all_handlers: List[EventHandler] = []
        self._event_queue: queue.Queue = queue.Queue()
        self._event_log: List[Event] = []
        self._max_log_size = 1000
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._initialized = True
    
    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler
    ) -> None:
        """Subscribe to specific event type."""
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler subscribed to {event_type.value}")
    
    def subscribe_all(self, handler: EventHandler) -> None:
        """Subscribe to all events."""
        self._all_handlers.append(handler)
        logger.debug("Handler subscribed to all events")
    
    def unsubscribe(
        self,
        event_type: EventType,
        handler: EventHandler
    ) -> None:
        """Unsubscribe from event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
    
    def publish(self, event: Event) -> None:
        """Publish event to subscribers."""
        self._event_queue.put(event)
        
        # Log event
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]
    
    def publish_sync(self, event: Event) -> None:
        """Publish event synchronously (blocking)."""
        self._dispatch_event(event)
        
        # Log event
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]
    
    def _dispatch_event(self, event: Event) -> None:
        """Dispatch event to handlers."""
        # Call specific handlers
        for handler in self._handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event.event_type}: {e}")
        
        # Call global handlers
        for handler in self._all_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Global handler error: {e}")
    
    def _worker(self) -> None:
        """Background worker for async event processing."""
        while self._running:
            try:
                event = self._event_queue.get(timeout=1.0)
                self._dispatch_event(event)
                self._event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def start(self) -> None:
        """Start async event processing."""
        if self._running:
            return
        
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()
        logger.info("EventBus started")
    
    def stop(self) -> None:
        """Stop async event processing."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        logger.info("EventBus stopped")
    
    def get_recent_events(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get recent events from log."""
        events = self._event_log
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return [e.to_dict() for e in events[-limit:]]
    
    def clear_log(self) -> None:
        """Clear event log."""
        self._event_log.clear()


class NotificationService:
    """
    Manages user notifications.
    """
    
    def __init__(self):
        self._notifications: Dict[int, List[Notification]] = defaultdict(list)
        self._max_per_user = 100
    
    def send(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        action_url: Optional[str] = None,
        data: Optional[Dict] = None
    ) -> Notification:
        """Send notification to user."""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            action_url=action_url,
            data=data or {}
        )
        
        self._notifications[user_id].append(notification)
        
        # Limit per user
        if len(self._notifications[user_id]) > self._max_per_user:
            self._notifications[user_id] = self._notifications[user_id][-self._max_per_user:]
        
        return notification
    
    def get_notifications(
        self,
        user_id: int,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict]:
        """Get user notifications."""
        notifications = self._notifications.get(user_id, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        return [n.to_dict() for n in notifications[-limit:]]
    
    def mark_read(self, user_id: int, index: int = None) -> int:
        """Mark notifications as read. Returns count of marked."""
        notifications = self._notifications.get(user_id, [])
        count = 0
        
        if index is not None:
            if 0 <= index < len(notifications):
                notifications[index].read = True
                count = 1
        else:
            for n in notifications:
                if not n.read:
                    n.read = True
                    count += 1
        
        return count
    
    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications."""
        notifications = self._notifications.get(user_id, [])
        return sum(1 for n in notifications if not n.read)
    
    def clear(self, user_id: int) -> int:
        """Clear all notifications for user."""
        count = len(self._notifications.get(user_id, []))
        self._notifications[user_id] = []
        return count


class ActivityLogger:
    """
    Logs user activities for analytics and debugging.
    """
    
    def __init__(self, event_bus: EventBus = None):
        self._activities: List[Dict] = []
        self._max_size = 5000
        
        # Subscribe to events
        if event_bus:
            event_bus.subscribe_all(self._log_event)
    
    def _log_event(self, event: Event) -> None:
        """Log event as activity."""
        activity = {
            "type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "user_id": event.user_id,
            "data": event.data
        }
        
        self._activities.append(activity)
        
        if len(self._activities) > self._max_size:
            self._activities = self._activities[-self._max_size:]
    
    def log(
        self,
        activity_type: str,
        user_id: Optional[int] = None,
        data: Optional[Dict] = None
    ) -> None:
        """Log custom activity."""
        activity = {
            "type": activity_type,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "data": data or {}
        }
        self._activities.append(activity)
    
    def get_activities(
        self,
        user_id: Optional[int] = None,
        activity_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get filtered activities."""
        activities = self._activities
        
        if user_id:
            activities = [a for a in activities if a.get("user_id") == user_id]
        
        if activity_type:
            activities = [a for a in activities if a.get("type") == activity_type]
        
        return activities[-limit:]
    
    def get_user_activity_summary(self, user_id: int) -> Dict[str, Any]:
        """Get summary of user activities."""
        user_activities = [
            a for a in self._activities
            if a.get("user_id") == user_id
        ]
        
        # Count by type
        type_counts = defaultdict(int)
        for a in user_activities:
            type_counts[a["type"]] += 1
        
        return {
            "user_id": user_id,
            "total_activities": len(user_activities),
            "activity_counts": dict(type_counts),
            "recent_activities": user_activities[-10:]
        }


# ==================== SINGLETON INSTANCES ====================

_event_bus: Optional[EventBus] = None
_notification_service: Optional[NotificationService] = None
_activity_logger: Optional[ActivityLogger] = None


def get_event_bus() -> EventBus:
    """Get singleton EventBus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
        _event_bus.start()
    return _event_bus


def get_notification_service() -> NotificationService:
    """Get singleton NotificationService instance."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service


def get_activity_logger() -> ActivityLogger:
    """Get singleton ActivityLogger instance."""
    global _activity_logger
    if _activity_logger is None:
        _activity_logger = ActivityLogger(get_event_bus())
    return _activity_logger


# ==================== CONVENIENCE FUNCTIONS ====================

def emit_event(
    event_type: EventType,
    data: Dict = None,
    user_id: int = None
) -> None:
    """Quick helper to emit an event."""
    event = Event(
        event_type=event_type,
        data=data or {},
        user_id=user_id
    )
    get_event_bus().publish(event)


def notify_user(
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "info"
) -> None:
    """Quick helper to send notification."""
    nt = NotificationType(notification_type)
    get_notification_service().send(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=nt
    )
