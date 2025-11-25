from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

# EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "teerdavenigedela@gmail.com"

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'teerdavenigedela@gmail.com'
EMAIL_HOST_PASSWORD = 'vcig blpb lbdg sact'