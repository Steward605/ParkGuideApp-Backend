from decimal import Decimal
import secrets
import string
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from accounts.models import CustomUser
from .models import PaymentRecord

def get_payment_expiry_time():
    days = getattr(settings, 'PAYMENT_LINK_EXPIRY_DAYS', 14)
    return timezone.now() + timezone.timedelta(days=days)

def get_default_payment_amount():
    raw_amount = getattr(settings, 'PARK_GUIDE_PAYMENT_AMOUNT', '50.00')
    return Decimal(str(raw_amount))

def generate_temporary_password(length=12):
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_unique_username_from_email(email):
    base = (email.split('@')[0] or 'parkguide').lower().replace(' ', '')
    base = ''.join(ch for ch in base if ch.isalnum() or ch in ('_', '.')) or 'parkguide'
    candidate = base
    index = 1
    while CustomUser.objects.filter(username=candidate).exists():
        candidate = f'{base}{index}'
        index += 1
    return candidate

def create_payment_record_for_application(application, approved_by=None):
    record, created = PaymentRecord.objects.get_or_create(
        application=application,
        defaults={
            'guide': None,
            'applicant_name': application.full_name,
            'applicant_email': application.email,
            'amount': get_default_payment_amount(),
            'currency': 'MYR',
            'status': PaymentRecord.STATUS_PENDING,
            'created_by': approved_by,
            'expires_at': get_payment_expiry_time(),
        },
    )
    if not created:
        record.applicant_name = application.full_name
        record.applicant_email = application.email
        if record.status in {PaymentRecord.STATUS_EXPIRED, PaymentRecord.STATUS_CANCELLED}:
            record.status = PaymentRecord.STATUS_PENDING
            record.expires_at = get_payment_expiry_time()
        record.save(update_fields=['applicant_name', 'applicant_email', 'status', 'expires_at', 'updated_at'])
    return record

def send_payment_link_email(payment_record, request=None):
    payment_url = payment_record.build_payment_url(request=request)
    subject = 'Park Guide application approved - payment required'
    message = (
        f'Hello {payment_record.applicant_name},\n\n'
        'Your Park Guide application has been approved.\n\n'
        'Please complete the registration payment using the link below:\n'
        f'{payment_url}\n\n'
        f'Payment reference: {payment_record.payment_reference}\n'
        f'Amount: {payment_record.currency} {payment_record.amount}\n'
        f'Expires at: {payment_record.expires_at.strftime("%Y-%m-%d %H:%M UTC") if payment_record.expires_at else "-"}\n\n'
        'After the mock payment is completed successfully, your park guide account will be created '
        'and your temporary login credentials will be emailed to you.\n\n'
        'This is a mock payment gateway for system testing only. No real payment will be charged.\n\n'
        'Regards,\n'
        'Park Guide Team'
    )
    send_mail(subject=subject, message=message, from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None), recipient_list=[payment_record.applicant_email], fail_silently=False,)
    return payment_url

@transaction.atomic
def issue_guide_account_after_payment(payment_record):
    payment_record = PaymentRecord.objects.select_for_update(of=('self',)).select_related('application').get(id=payment_record.id)
    if payment_record.status != PaymentRecord.STATUS_PAID:
        raise ValueError('Guide account can only be issued after payment is marked as paid.')
    application = payment_record.application
    if not application:
        raise ValueError('This payment record is not linked to an application.')
    if payment_record.guide:
        return payment_record.guide, None, False
    if application.approved_user:
        payment_record.guide = application.approved_user
        payment_record.save(update_fields=['guide', 'updated_at'])
        return application.approved_user, None, False
    existing_user = CustomUser.objects.filter(email=application.email).first()
    if existing_user:
        application.approved_user = existing_user
        application.save(update_fields=['approved_user', 'updated_at'])
        payment_record.guide = existing_user
        payment_record.save(update_fields=['guide', 'updated_at'])
        return existing_user, None, False
    temp_password = generate_temporary_password()
    username = generate_unique_username_from_email(application.email)
    name_parts = application.full_name.split(' ', 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ''
    new_user = CustomUser.objects.create_user(
        username=username,
        email=application.email,
        password=temp_password,
        first_name=first_name,
        last_name=last_name,
        phone_number=application.phone_number,
        birthdate=application.birthdate,
        is_staff=False,
        must_change_password=True,
    )
    application.approved_user = new_user
    application.save(update_fields=['approved_user', 'updated_at'])
    payment_record.guide = new_user
    payment_record.save(update_fields=['guide', 'updated_at'])
    return new_user, temp_password, True

def send_guide_credentials_email(payment_record, guide, temp_password):
    if not temp_password:
        return
    subject = 'Your Park Guide account has been created'
    message = (
        f'Hello {payment_record.applicant_name},\n\n'
        'Your mock payment has been completed successfully.\n\n'
        'Your Park Guide account has now been created.\n\n'
        'Temporary account details:\n'
        f'Email: {guide.email}\n'
        f'Password: {temp_password}\n\n'
        'Please sign in and change your password on your first login.\n\n'
        f'Payment reference: {payment_record.payment_reference}\n'
        f'Mock transaction ID: {payment_record.mock_transaction_id or "-"}\n\n'
        'Regards,\n'
        'Park Guide Team'
    )
    send_mail(subject=subject, message=message, from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None), recipient_list=[guide.email], fail_silently=True)