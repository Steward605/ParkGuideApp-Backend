from decimal import Decimal
import secrets
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

def generate_payment_token():
    return secrets.token_urlsafe(32)

def generate_payment_reference():
    date_part = timezone.now().strftime('%Y%m%d')
    random_part = secrets.token_hex(4).upper()
    return f'PGP-{date_part}-{random_part}'

class PaymentRecord(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_EXPIRED = 'expired'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = ((STATUS_PENDING, 'Pending'), (STATUS_PAID, 'Paid'), (STATUS_EXPIRED, 'Expired'), (STATUS_CANCELLED, 'Cancelled'))
    application = models.OneToOneField('accounts.AccountApplication', null=True, blank=True, on_delete=models.SET_NULL, related_name='payment_record',)
    guide = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='payment_records',)
    applicant_name = models.CharField(max_length=255)
    applicant_email = models.EmailField(db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('50.00'))
    currency = models.CharField(max_length=10, default='MYR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True,)
    public_token = models.CharField(max_length=128, unique=True, db_index=True, default=generate_payment_token,)
    payment_reference = models.CharField(max_length=50, unique=True, db_index=True, default=generate_payment_reference,)
    mock_transaction_id = models.CharField(max_length=80, blank=True, default='')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_payment_records',)
    metadata = models.JSONField(default=dict, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.payment_reference} - {self.applicant_email} - {self.status}'

    @property
    def is_expired(self):
        return bool(self.expires_at and self.status == self.STATUS_PENDING and self.expires_at <= timezone.now())

    def build_payment_url(self, request=None):
        path = reverse('payments:mock_payment_gate', kwargs={'token': self.public_token})
        if request is not None:
            return request.build_absolute_uri(path)
        base_url = getattr(settings, 'PUBLIC_BACKEND_BASE_URL', '').rstrip()
        if base_url:
            return f'{base_url}{path}'
        return path

    def mark_expired(self):
        if self.status == self.STATUS_PENDING:
            self.status = self.STATUS_EXPIRED
            self.save(update_fields=['status', 'updated_at'])

    def mark_paid(self, request=None):
        if self.status == self.STATUS_PAID:
            return
        now = timezone.now()
        self.status = self.STATUS_PAID
        self.paid_at = now
        if not self.mock_transaction_id:
            self.mock_transaction_id = f'MOCK-{now.strftime("%Y%m%d%H%M%S")}-{secrets.token_hex(3).upper()}'
        metadata = dict(self.metadata or {})
        if request is not None:
            metadata['paid_ip'] = request.META.get('REMOTE_ADDR', '')
            metadata['paid_user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        metadata['payment_mode'] = 'mock'
        metadata['paid_at_iso'] = now.isoformat()
        self.metadata = metadata
        self.save(update_fields=['status', 'paid_at', 'mock_transaction_id', 'metadata', 'updated_at',])