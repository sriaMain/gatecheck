from django.db import models
from django.contrib.auth.models import AbstractUser



class Company(models.Model):
    company_name = models.CharField(max_length = 255, unique=True)
    address = models.TextField()
    location = models.CharField(max_length=255)
    pin_code = models.CharField(max_length=10)

    def __str__(self):
        return self.company_name
    


class CustomUser(AbstractUser):
    user_id = models.CharField(max_length=15, unique=True)
    username = models.CharField(max_length=150, unique=True)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, related_name='company_users')
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=15, blank=True)
    alias_name = models.CharField(max_length=50, blank=True)
    block = models.CharField(max_length=50, blank=True)
    floor = models.CharField(max_length=50, blank=True)
    # role = models.ForeignKey("roles_creation.Role", on_delete=models.SET_NULL, null=True, related_name='users')
    

    def __str__(self):
        return self.email





