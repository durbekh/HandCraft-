"""
URL patterns for the messaging app.
"""

from django.urls import path

from . import views

app_name = "messaging"

urlpatterns = [
    path(
        "conversations/",
        views.ConversationListView.as_view(),
        name="conversation-list",
    ),
    path(
        "conversations/create/",
        views.ConversationCreateView.as_view(),
        name="conversation-create",
    ),
    path(
        "conversations/<uuid:pk>/",
        views.ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path(
        "conversations/<uuid:pk>/send/",
        views.SendMessageView.as_view(),
        name="send-message",
    ),
    path(
        "conversations/<uuid:pk>/read/",
        views.MarkConversationReadView.as_view(),
        name="mark-read",
    ),
    path(
        "conversations/<uuid:pk>/archive/",
        views.ArchiveConversationView.as_view(),
        name="archive-conversation",
    ),
    path(
        "unread-count/",
        views.UnreadCountView.as_view(),
        name="unread-count",
    ),
]
