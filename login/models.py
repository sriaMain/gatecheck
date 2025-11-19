from django.db import models
import random
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=6, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.otp:
            self.otp = str(random.randint(100000, 999999))
        super().save(*args, **kwargs)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.created_at + timedelta(minutes=15)

    def __str__(self):
        return f"{self.user.email} - {self.otp}"
