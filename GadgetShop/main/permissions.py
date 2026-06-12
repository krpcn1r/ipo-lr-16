from rest_framework.permissions import BasePermission, SAFE_METHODS


def user_is_admin(user):
    if not (user and user.is_authenticated):
        return False
    if user.is_staff or user.is_superuser:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role == "ADMIN")


class IsAdminOrReadOnly(BasePermission):

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return user_is_admin(request.user)
