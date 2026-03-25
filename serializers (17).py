"""
Serializers for the messaging app.
"""

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import serializers

from .models import Conversation, Message

User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for individual messages."""

    sender_name = serializers.CharField(
        source="sender.get_full_name", read_only=True
    )
    sender_avatar = serializers.ImageField(
        source="sender.avatar", read_only=True
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "sender_name",
            "sender_avatar",
            "content",
            "attachment",
            "is_read",
            "read_at",
            "is_system_message",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "conversation",
            "sender",
            "is_read",
            "read_at",
            "is_system_message",
            "created_at",
        ]


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new message."""

    class Meta:
        model = Message
        fields = ["content", "attachment"]

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        return value


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer for conversation listings."""

    other_participant = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    related_product_title = serializers.CharField(
        source="related_product.title", read_only=True, default=None
    )

    class Meta:
        model = Conversation
        fields = [
            "id",
            "subject",
            "other_participant",
            "related_product",
            "related_product_title",
            "related_order",
            "last_message",
            "unread_count",
            "last_message_at",
            "created_at",
        ]

    def get_other_participant(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        other = obj.get_other_participant(request.user)
        if other:
            return {
                "id": str(other.id),
                "full_name": other.get_full_name(),
                "avatar": other.avatar.url if other.avatar else None,
                "role": other.role,
            }
        return None

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        if last:
            return {
                "content": last.content[:100],
                "sender_name": last.sender.get_full_name(),
                "created_at": last.created_at,
                "is_read": last.is_read,
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if request:
            return obj.get_unread_count(request.user)
        return 0


class ConversationDetailSerializer(serializers.ModelSerializer):
    """Serializer for conversation detail with messages."""

    messages = MessageSerializer(many=True, read_only=True)
    participants_info = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "subject",
            "participants_info",
            "related_product",
            "related_order",
            "messages",
            "is_archived",
            "created_at",
        ]

    def get_participants_info(self, obj):
        return [
            {
                "id": str(p.id),
                "full_name": p.get_full_name(),
                "avatar": p.avatar.url if p.avatar else None,
                "role": p.role,
            }
            for p in obj.participants.all()
        ]


class ConversationCreateSerializer(serializers.Serializer):
    """Serializer for starting a new conversation."""

    recipient_id = serializers.UUIDField()
    subject = serializers.CharField(max_length=255, required=False, default="")
    message = serializers.CharField(max_length=5000)
    related_product_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_recipient_id(self, value):
        try:
            recipient = User.objects.get(id=value, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("Recipient not found.")

        request = self.context.get("request")
        if request and str(request.user.id) == str(value):
            raise serializers.ValidationError(
                "You cannot start a conversation with yourself."
            )
        return value

    def create(self, validated_data):
        request = self.context["request"]
        sender = request.user
        recipient = User.objects.get(id=validated_data["recipient_id"])

        # Check if conversation already exists between these users
        existing = Conversation.objects.filter(
            participants=sender
        ).filter(participants=recipient)

        if validated_data.get("related_product_id"):
            existing = existing.filter(
                related_product_id=validated_data["related_product_id"]
            )

        if existing.exists():
            conversation = existing.first()
        else:
            conversation = Conversation.objects.create(
                subject=validated_data.get("subject", ""),
            )
            conversation.participants.add(sender, recipient)

            if validated_data.get("related_product_id"):
                from apps.products.models import Product

                try:
                    product = Product.objects.get(
                        id=validated_data["related_product_id"]
                    )
                    conversation.related_product = product
                    conversation.save(update_fields=["related_product"])
                except Product.DoesNotExist:
                    pass

        # Create the first message
        Message.objects.create(
            conversation=conversation,
            sender=sender,
            content=validated_data["message"],
        )

        return conversation
