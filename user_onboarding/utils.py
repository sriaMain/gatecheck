from django.core.mail import send_mail
import random
from django.contrib.auth.hashers import make_password
from .models import CustomUser
from roles_creation.models import Role  # Assuming Role model is in roles_creation app
from .tasks import send_credentials_email
import string




def generate_user_id():
    return str(random.randint(100000000, 999999999))

# 
def generate_password(length=6):
    characters = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return ''.join(random.choices(characters, k=length))
def create_user_and_send_mail(username, email, company, mobile_number='', alias_name='', block='', floor='', role=None):
    from django.contrib.auth.hashers import make_password
    if isinstance(role, int):
        role = Role.objects.filter(id=role).first()

    user_id = str(random.randint(100000000, 999999999))
    raw_password = generate_password()
    # raw_password = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz1234567890', k=6))

    user = CustomUser.objects.create(
        username=username,  # Use email prefix as username
        email=email,
        user_id=user_id,
        password=make_password(raw_password),
        company=company,
        mobile_number=mobile_number,
        alias_name=alias_name,
        block=block,
        floor=floor,
        # role=role
    )

    send_credentials_email.delay(email, user_id, raw_password, username)
    return user
