"""
Elasticsearch document definitions for the products app.

Indexes products for full-text search with filters and autocomplete.
"""

from django_elasticsearch_dsl import Document, Index, fields
from django_elasticsearch_dsl.registries import registry

from .models import Product

PRODUCT_INDEX = Index("products")
PRODUCT_INDEX.settings(
    number_of_shards=1,
    number_of_replicas=0,
    max_result_window=50000,
    analysis={
        "analyzer": {
            "autocomplete_analyzer": {
                "type": "custom",
                "tokenizer": "autocomplete_tokenizer",
                "filter": ["lowercase"],
            },
            "search_analyzer": {
                "type": "custom",
                "tokenizer": "standard",
                "filter": ["lowercase"],
            },
        },
        "tokenizer": {
            "autocomplete_tokenizer": {
                "type": "edge_ngram",
                "min_gram": 2,
                "max_gram": 15,
                "token_chars": ["letter", "digit"],
            },
        },
    },
)


@registry.register_document
@PRODUCT_INDEX.doc_type
class ProductDocument(Document):
    """Elasticsearch document for Product model."""

    # Main fields
    title = fields.TextField(
        analyzer="autocomplete_analyzer",
        search_analyzer="search_analyzer",
        fields={
            "raw": fields.KeywordField(),
            "suggest": fields.CompletionField(),
        },
    )
    description = fields.TextField(analyzer="standard")
    short_description = fields.TextField(analyzer="standard")
    materials = fields.TextField(analyzer="standard")

    # Keyword/filterable fields
    slug = fields.KeywordField()
    status = fields.KeywordField()
    sku = fields.KeywordField()

    # Numeric fields
    price = fields.FloatField()
    compare_at_price = fields.FloatField()
    stock_quantity = fields.IntegerField()
    average_rating = fields.FloatField()
    total_reviews = fields.IntegerField()
    total_sales = fields.IntegerField()
    view_count = fields.IntegerField()

    # Boolean fields
    is_active = fields.BooleanField()
    is_featured = fields.BooleanField()
    is_free_shipping = fields.BooleanField()
    is_customizable = fields.BooleanField()

    # Date fields
    created_at = fields.DateField()

    # Nested / related fields
    artisan = fields.ObjectField(
        properties={
            "id": fields.KeywordField(),
            "full_name": fields.TextField(),
            "email": fields.KeywordField(),
        }
    )
    category = fields.ObjectField(
        properties={
            "id": fields.KeywordField(),
            "name": fields.TextField(
                analyzer="autocomplete_analyzer",
                search_analyzer="search_analyzer",
            ),
            "slug": fields.KeywordField(),
        }
    )
    tags = fields.ObjectField(
        properties={
            "name": fields.TextField(),
            "slug": fields.KeywordField(),
        }
    )
    primary_image_url = fields.KeywordField()
    artisan_shop_name = fields.TextField(
        analyzer="autocomplete_analyzer",
        search_analyzer="search_analyzer",
    )
    artisan_country = fields.KeywordField()

    class Django:
        model = Product
        related_models = []

    def prepare_artisan(self, instance):
        return {
            "id": str(instance.artisan.id),
            "full_name": instance.artisan.get_full_name(),
            "email": instance.artisan.email,
        }

    def prepare_category(self, instance):
        if instance.category:
            return {
                "id": str(instance.category.id),
                "name": instance.category.name,
                "slug": instance.category.slug,
            }
        return None

    def prepare_tags(self, instance):
        return [
            {"name": tag.name, "slug": tag.slug}
            for tag in instance.tags.all()
        ]

    def prepare_primary_image_url(self, instance):
        primary = instance.images.filter(is_primary=True).first()
        if not primary:
            primary = instance.images.first()
        if primary and primary.image:
            return primary.image.url
        return ""

    def prepare_artisan_shop_name(self, instance):
        try:
            return instance.artisan.artisan_profile.shop_name
        except Exception:
            return ""

    def prepare_artisan_country(self, instance):
        try:
            return instance.artisan.artisan_profile.location_country
        except Exception:
            return ""

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("artisan", "category")
            .prefetch_related("tags", "images")
            .filter(is_active=True, status=Product.Status.ACTIVE)
        )
