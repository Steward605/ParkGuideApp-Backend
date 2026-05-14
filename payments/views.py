from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from django.db import transaction
from .models import PaymentRecord
from .services import issue_guide_account_after_payment, send_guide_credentials_email

@require_http_methods(['GET', 'POST'])
def mock_payment_gate(request, token):
    payment = get_object_or_404(PaymentRecord.objects.select_related('guide', 'application'), public_token=token,)
    if payment.is_expired:
        payment.mark_expired()
    if request.method == 'POST':
        if payment.status == PaymentRecord.STATUS_PAID:
            return redirect('payments:payment_success', token=payment.public_token)
        if payment.status != PaymentRecord.STATUS_PENDING:
            messages.error(request, 'This payment link is no longer available.')
            return redirect('payments:mock_payment_gate', token=payment.public_token)
        if payment.is_expired:
            payment.mark_expired()
            messages.error(request, 'This payment link has expired.')
            return redirect('payments:mock_payment_gate', token=payment.public_token)
        try:
            with transaction.atomic():
                payment.mark_paid(request=request)
                guide, temp_password, created = issue_guide_account_after_payment(payment)
            if created:
                send_guide_credentials_email(payment_record=payment, guide=guide, temp_password=temp_password,)
        except Exception as exc:
            messages.error(request, f'Payment could not be completed because the guide account could not be created: {exc}')
            return redirect('payments:mock_payment_gate', token=payment.public_token)
        return redirect('payments:payment_success', token=payment.public_token)
    return render(request, 'payments/mock_payment_gate.html', {
        'payment': payment,
    })

@require_http_methods(['GET'])
def payment_success(request, token):
    payment = get_object_or_404(PaymentRecord.objects.select_related('guide', 'application'), public_token=token,)
    return render(request, 'payments/payment_success.html', {
        'payment': payment,
    })