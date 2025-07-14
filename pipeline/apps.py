from django.apps import AppConfig


class PipelineConfig(AppConfig):
    """Pipeline app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "pipeline"
    verbose_name = "Domain Discovery Pipeline"
