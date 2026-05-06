from secrets import token_urlsafe
from django.conf import settings


class SecurityHeadersMiddleware:
    """
    Add security headers not covered by Django's built-in middleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.csp_nonce = token_urlsafe(16)
        response = self.get_response(request)
        response.setdefault("Content-Security-Policy", self._content_security_policy(request))
        response.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        return response

    @staticmethod
    def _content_security_policy(request):
        nonce = getattr(request, "csp_nonce", "")
        directives = [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net",
            "script-src-attr 'none'",
            f"style-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "style-src-attr 'none'",
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com data:",
            "img-src 'self' data: blob:",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
        if getattr(settings, "CSP_UPGRADE_INSECURE_REQUESTS", False):
            directives.append("upgrade-insecure-requests")
        return "; ".join(directives)
