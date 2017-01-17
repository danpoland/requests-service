from requests.auth import AuthBase


class JwtAuth(AuthBase):
    """
    Attaches the JWT Authorization header to the given Request object.
    """

    def __init__(self, token):
        self._token = token

    def __call__(self, r):
        r.headers['Authorization'] = 'JWT %s' % self._token
        return r
