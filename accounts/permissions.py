from rest_framework import permissions

# central RBAC permission classes
# role based access checks should import from here.

class IsAdmin(permissions.BasePermission):
    # grants access to staff, superuser and users with 'admin' type.
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (
                request.user.is_staff or
                request.user.is_superuser or
                request.user.user_type == 'admin'
            )
        )


class IsLearner(permissions.BasePermission):
    # grants access to user and users with 'learner' type.
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.user_type == 'learner'
        )
