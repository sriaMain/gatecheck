from .base import *
import os

DEBUG = True
ALLOWED_HOSTS = ["*"]

# ✅ Database for local development (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ✅ Email settings for local development (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'teerdavenigedela@gmail.com'
EMAIL_HOST_PASSWORD = 'vcig blpb lbdg sact'  # Gmail App Password
DEFAULT_FROM_EMAIL = "teerdavenigedela@gmail.com"

# ✅ Use local filesystem for media
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

print("🔧 LOCAL SETTINGS LOADED")
print(f"📧 Email backend: {EMAIL_BACKEND}")
print("💾 Database: SQLite")
print("📁 Media storage: Local filesystem")