from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


# Аутенификация по токену
def auth_user(request):
    auth = TokenAuthentication()
    try:
        user_auth_tuple = auth.authenticate(request)
        if user_auth_tuple:
            request.user, request.auth = user_auth_tuple
    except AuthenticationFailed:
        pass
    finally:
        return request
