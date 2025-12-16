from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid
from django.conf import settings




class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)



class User(AbstractUser):
    USER_TYPES = [
        ('normal', 'Land Appraiser'),
        ('scientist', 'Data Scientist'),
        ('admin', 'Admin'),
    ]

    username = None  
    name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(unique=True)
    type = models.CharField(max_length=20, choices=USER_TYPES, default='normal')
    phone = models.CharField(max_length=20, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  

    objects = CustomUserManager()

    def __str__(self):
        return self.email



class ActivationCode(models.Model):
    USER_TYPES = [
        ('normal', 'Normal User (Appraiser)'),
        ('data_scientist', 'Data Scientist'),
        ('admin', 'Administrator'),
    ]

    code = models.CharField(max_length=50, unique=True)
    user_type = models.CharField(max_length=30, choices=USER_TYPES)
    is_used = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
       return f"{self.code} ({self.get_user_type_display()})"

    @classmethod
    def generate_code(cls, user_type):
        """Generate and save a unique activation code."""
        code = uuid.uuid4().hex[:8].upper()
        return cls.objects.create(code=code, user_type=user_type)