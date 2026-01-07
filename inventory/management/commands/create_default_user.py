from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = "Create default user if not exists"

    def handle(self, *args, **kwargs):
        username = os.getenv("DEFAULT_ADMIN_USERNAME", "helmet")
        password = os.getenv("DEFAULT_ADMIN_PASSWORD", "helmet@2025")

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                password=password,
                email=""
            )
            self.stdout.write(self.style.SUCCESS("Default admin user created"))
        else:
            self.stdout.write("Default admin user already exists")
