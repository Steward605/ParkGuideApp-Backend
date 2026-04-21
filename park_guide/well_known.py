from django.conf import settings
from django.http import JsonResponse


def assetlinks_json(request):
    payload = [
        {
            "relation": ["delegate_permission/common.get_login_creds"],
            "target": {
                "namespace": "android_app",
                "package_name": settings.PASSKEY_ANDROID_PACKAGE_NAME,
                "sha256_cert_fingerprints": [settings.PASSKEY_ANDROID_SHA256],
            },
        }
    ]
    return JsonResponse(payload, safe=False)
