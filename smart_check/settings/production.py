from .base import *
import os

DEBUG = False
# ALLOWED_HOSTS = ["*"]


EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

DEFAULT_FROM_EMAIL = "teerdavenigedela@gmail.com"

SENDGRID_SANDBOX_MODE_IN_DEBUG = False
SENDGRID_ECHO_TO_STDOUT = False


import os
import dj_database_url

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }

# INSTALLED_APPS += [
#     "cloudinary",
#     "cloudinary_storage",
# ]


CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get("CLOUDINARY_CLOUD_NAME"),
    'API_KEY': os.environ.get("CLOUDINARY_API_KEY"),
    'API_SECRET': os.environ.get("CLOUDINARY_API_SECRET"),
    'SECURE': True,
    'AUTHENTICATED': False,
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ✅ Cloudinary media configuration
MEDIA_ROOT = BASE_DIR / 'media'  # Fallback/temp path

# Don't set MEDIA_URL - let cloudinary_storage generate the correct URL automatically
# The package will create URLs like: https://res.cloudinary.com/{cloud_name}/image/upload/{path}

print("Using Cloudinary for media storage in production.")