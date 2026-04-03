from security.models import Permission

def get_permission(user, module_name):
    try:
        role = user.userprofile.role
        return Permission.objects.get(role=role, module__name=module_name)
    except:
        return None