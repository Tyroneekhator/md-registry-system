# apps/accounts/signals.py
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Users, Groups, UserGroups  # your custom tables


User = get_user_model()


@receiver(post_save, sender=User)
def sync_django_user_to_custom_users(sender, instance, created, **kwargs):
    """
    Keep apps.accounts.models.Users in sync with Django's auth user.
    This allows a Django superuser to also log into /accounts/login/.
    """
    # We sync all staff/superusers (you can change this to sync all users if you want)
    if not (instance.is_staff or instance.is_superuser):
        return

    # Create/update the custom Users row
    custom_user, _ = Users.objects.update_or_create(
        Username=instance.username,
        defaults={
            # Store Django's hashed password (pbkdf2_sha256$...).
            # Your login view uses check_password(), so this works perfectly.
            "PasswordHash": instance.password,
            "IsActive": instance.is_active,
            "LastLoginAt": timezone.now() if instance.last_login else None,
        },
    )

    # Optional but recommended: ensure superuser is in the "Admin" group in your tables
    if instance.is_superuser:
        admin_group, _ = Groups.objects.get_or_create(GroupName="Admin")
        UserGroups.objects.get_or_create(UserID=custom_user, GroupID=admin_group)
