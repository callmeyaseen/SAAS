from security.utils import get_permission

def sidebar_permissions(request):
    if request.user.is_authenticated:
        vendor_perm = get_permission(request.user, "Vendor")
    else:
        vendor_perm = None

    return {
        "vendor_perm": vendor_perm,
    }