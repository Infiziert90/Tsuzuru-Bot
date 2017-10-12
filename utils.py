def get_role_by_id(server, role_id):
    for role in server.roles:
        if role.id == role_id:
            return role
    return None


def has_role(user, role_id):
    return get_role_by_id(user, role_id) is not None
