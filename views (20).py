"""
Views for the messaging app.
"""

from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Message
from .serializers import (
    ConversationCreateSerializer,
    ConversationDetailSerializer,
    ConversationListSerializer,
    MessageCreateSerializer,
    MessageSerializer,
)


class ConversationListView(generics.ListAPIView):
    """List conversations for the authenticated user."""

    serializer_class = ConversationListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            Conversation.objects.filter(
                participants=self.request.user,
                is_archived=False,
            )
            .prefetch_related("participants", "messages")
            .distinct()
        )


class ConversationCreateView(APIView):
    """Start a new conversation or continue existing one."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ConversationCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()

        return Response(
            ConversationDetailSerializer(
                conversation, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )


class ConversationDetailView(APIView):
    """Get conversation detail with all messages."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            conversation = Conversation.objects.prefetch_related(
                "participants", "messages__sender"
            ).get(pk=pk, participants=request.user)
        except Conversation.DoesNotExist:
            return Response(
                {"detail": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Mark unread messages as read
        conversation.messages.filter(is_read=False).exclude(
            sender=request.user
        ).update(is_read=True, read_at=timezone.now())

        serializer = ConversationDetailSerializer(
            conversation, context={"request": request}
        )
        return Response(serializer.data)


class SendMessageView(APIView):
    """Send a message in an existing conversation."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            conversation = Conversation.objects.get(
                pk=pk, participants=request.user
            )
        except Conversation.DoesNotExist:
            return Response(
                {"detail": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.save(
            conversation=conversation,
            sender=request.user,
        )

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


class MarkConversationReadView(APIView):
    """Mark all messages in a conversation as read."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            conversation = Conversation.objects.get(
                pk=pk, participants=request.user
            )
        except Conversation.DoesNotExist:
            return Response(
                {"detail": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        updated = conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).update(
            is_read=True, read_at=timezone.now()
        )

        return Response(
            {"marked_read": updated},
            status=status.HTTP_200_OK,
        )


class ArchiveConversationView(APIView):
    """Archive a conversation."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            conversation = Conversation.objects.get(
                pk=pk, participants=request.user
            )
        except Conversation.DoesNotExist:
            return Response(
                {"detail": "Conversation not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        conversation.is_archived = True
        conversation.save(update_fields=["is_archived"])

        return Response(
            {"message": "Conversation archived."},
            status=status.HTTP_200_OK,
        )


class UnreadCountView(APIView):
    """Get total unread message count for the authenticated user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        unread_count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False,
        ).exclude(sender=request.user).count()

        return Response({"unread_count": unread_count})
