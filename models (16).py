"""
Messaging models for HandCraft.

Defines Conversation and Message for buyer-seller communication.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Conversation(models.Model):
    """
    A conversation between two users (typically a customer and an artisan).
    Can be linked to a product or custom order request for context.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="conversations",
    )
    subject = models.CharField(_("subject"), max_length=255, blank=True)
    # Optional context links
    related_product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        related_name="conversations",
        blank=True,
        null=True,
    )
    related_order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        related_name="conversations",
        blank=True,
        null=True,
    )
    is_archived = models.BooleanField(_("archived"), default=False)
    last_message_at = models.DateTimeField(
        _("last message at"), blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("conversation")
        verbose_name_plural = _("conversations")
        ordering = ["-last_message_at", "-created_at"]

    def __str__(self):
        participant_names = ", ".join(
            p.get_full_name() for p in self.participants.all()[:2]
        )
        return f"Conversation: {self.subject or participant_names}"

    @property
    def unread_count_for(self):
        """Returns a method to get unread count for a specific user."""
        return self._unread_count_for

    def get_unread_count(self, user):
        """Get count of unread messages for a specific user."""
        return self.messages.filter(is_read=False).exclude(sender=user).count()

    def get_other_participant(self, user):
        """Get the other participant in the conversation."""
        return self.participants.exclude(id=user.id).first()


class Message(models.Model):
    """Individual message within a conversation."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    content = models.TextField(_("content"), max_length=5000)
    attachment = models.FileField(
        _("attachment"),
        upload_to="messages/%Y/%m/",
        blank=True,
        null=True,
    )
    is_read = models.BooleanField(_("read"), default=False)
    read_at = models.DateTimeField(_("read at"), blank=True, null=True)
    is_system_message = models.BooleanField(
        _("system message"),
        default=False,
        help_text=_("Automatically generated messages (e.g., order updates)."),
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = _("message")
        verbose_name_plural = _("messages")
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
        ]

    def __str__(self):
        return (
            f"Message from {self.sender.get_full_name()} "
            f"at {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update conversation's last_message_at
        from django.utils import timezone

        Conversation.objects.filter(pk=self.conversation_id).update(
            last_message_at=timezone.now()
        )
