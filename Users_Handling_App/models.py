from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager




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
        ('normal', 'Normal User'),
        ('scientist', 'Data Scientist'),
        ('admin', 'Admin'),
    ]

    username = None  
    name = models.CharField(max_length=200, null=True)
    email = models.EmailField(unique=True, null=True)
    type = models.CharField(max_length=20, choices=USER_TYPES, default='normal')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  

    objects = CustomUserManager()

    def __str__(self):
        return self.email
