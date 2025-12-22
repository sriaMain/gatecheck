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

# ✅ Cloudinary configuration for local development
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get("CLOUDINARY_CLOUD_NAME", "dngaxesdz"),
    'API_KEY': os.environ.get("CLOUDINARY_API_KEY"),
    'API_SECRET': os.environ.get("CLOUDINARY_API_SECRET"),
    'SECURE': True,
    'AUTHENTICATED': False,
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
MEDIA_ROOT = BASE_DIR / 'media'  # Fallback/temp path
# Don't set MEDIA_URL - let cloudinary_storage generate the correct URL

print("🔧 LOCAL SETTINGS LOADED")
print(f"📧 Email backend: {EMAIL_BACKEND}")
print("💾 Database: SQLite")
print(f"📁 Media storage: Cloudinary ({CLOUDINARY_STORAGE.get('CLOUD_NAME', 'NOT SET')})")


from django.utils import timezone
import pytz

ist = pytz.timezone("Asia/Kolkata")
CURRENT_TIME = timezone.now().astimezone(ist)