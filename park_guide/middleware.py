from django.conf import settings


class SecurityHeadersMiddleware:
    """Add security headers not covered by Django's built-in middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        response.setdefault('Content-Security-Policy', self._content_security_policy(request))
        response.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')

        return response

    def _content_security_policy(self, request):
        if self._is_strict_csp_path(request):
            return self._strict_content_security_policy()

        return self._legacy_content_security_policy()

    @staticmethod
    def _is_strict_csp_path(request):
        return request.path == '/login/'

    @staticmethod
    def _legacy_content_security_policy():
        directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://cdn.jsdelivr.net https://fonts.gstatic.com data:",
            "img-src 'self' data: blob:",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]

        if getattr(settings, 'CSP_UPGRADE_INSECURE_REQUESTS', False):
            directives.append('upgrade-insecure-requests')

        return '; '.join(directives)

    @staticmethod
    def _strict_content_security_policy():
        directives = [
            "default-src 'self'",
            "script-src 'self'",
            "style-src 'self' https://cdn.jsdelivr.net",
            "font-src 'self' https://cdn.jsdelivr.net data:",
            "img-src 'self' data:",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]

        if getattr(settings, 'CSP_UPGRADE_INSECURE_REQUESTS', False):
            directives.append('upgrade-insecure-requests')

        return '; '.join(directives)
