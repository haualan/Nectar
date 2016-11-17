from rest_framework import permissions
from profiles.models import User


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the snippet.
        if isinstance(obj, User): 
            # print 'USer obj perm', obj.email, request.user,  obj == request.user
            return obj == request.user
        return obj.user == request.user

class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow Read for everyone but edit for admin only
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the snippet.
        return request.user.is_staff

