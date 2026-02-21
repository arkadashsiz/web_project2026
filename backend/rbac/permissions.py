from rest_framework.permissions import BasePermission


def user_has_action(user, action: str) -> bool:
    if user.is_superuser:
        return True
    return user.user_roles.filter(role__permissions__action=action).exists()


class HasActionPermission(BasePermission):
    action_name = None

    def has_permission(self, request, view):
        action = getattr(view, 'required_action', None) or self.action_name
        if not action:
            return True
        return request.user.is_authenticated and user_has_action(request.user, action)
