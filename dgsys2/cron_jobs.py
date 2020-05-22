import datetime

from dgsys2.models import User


def reset_expired_memberships():
    now = datetime.now()
    expired_users = User.objects.filter(
        membership_expiry__lte=now,
    )
    null_expiry_users = User.objects.filter(
        membership_expiry__isnull=True,
    )
    expired_users.update(membership=1)
    null_expiry_users.update(membership=1)


def reset_plus_members():
    User.objects.filter(membership=3).update(membership=2)
    print("Plus members reset")