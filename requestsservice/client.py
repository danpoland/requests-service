import requests

__all__ = [
    'HttpClientException',
    'HttpClient',
]


class HttpClientException(Exception):
    """
    Basic exception for wrapping Requests Responses into throwable exceptions when the response.status_code is >= 300.
    """

    def __init__(self, response):
        """
        :param response: Requests Response object
        """

        self.response = response


class SessionCache:
    """
    Simple caching mechanism for Request Sessions, allows us to keep the Session connection pools open.
    """

    __sessions = {}

    @classmethod
    def get(cls, name):
        return cls.__sessions.get(name)

    @classmethod
    def set(cls, name, session):
        cls.__sessions[name] = session


class HttpClient:
    """
    Http client used to consume HTTP APIs.
    Wraps the construction of Requests ``Request`` objects and returns Response instances.

    Factory Attributes:
        _service_root     The absolute URL path to the service being accessed.
        _default_headers  A dictionary of default headers to be persisted on the Session used to make requests.
        _timeout          A default timeout int or tuple (connect, read) to be used on every request.
        _max_retires      The maximum number of retries allowed before a request fails.
        _auth             The default AuthBase callable to be used with every request.
    """

    _service_root = ''
    _default_headers = {}
    _timeout = (3, 10)
    _max_retires = 3
    _auth = None

    @classmethod
    def make_client(cls, auth_kwargs=None):
        """
        Factory method for creating a new instance of the client.

        :param auth_kwargs: dict of kwargs that will be passed to the AuthBase callable used by the factory.
                            The auth is not used by the session but is used by every request made by the HttpService
                            instance (auth is not persisted with the session).
        :return: HTTPClient object.
        """

        session = SessionCache.get(cls.__name__)

        if not session:
            adapter = requests.adapters.HTTPAdapter(max_retries=cls._max_retires)
            session = requests.Session()

            session.mount('http://', adapter=adapter)
            session.mount('https://', adapter=adapter)
            session.headers.update(cls._default_headers)

            SessionCache.set(cls.__name__, session)

        auth = cls._auth

        if auth:
            auth = auth(**auth_kwargs) if auth_kwargs else auth()

        return cls(cls._service_root, session, auth)

    def __init__(self, url_root, session=None, auth=None, timeout=None):
        """
        :param url_root: The URI root of the service to communicate with.
        :param session: Optional, Requests Session object to be used to execute requests.
        :param auth: Requests AuthBase callable, this is not persisted on the session but will be used
                     by every request made from the HttpService instance.
        :param timeout: A default timeout int or tuple (connect, read) to be used on every request unless overridden.
        """

        self._url_root = None
        self.url_root = url_root
        self._requestor = session if session else requests.request
        self._auth = auth
        self._timeout = timeout

    def _build_url(self, path='', **path_params):
        """
        :param path: Appended to the end of _url_root. Supports {param_name} replacement.
        :param path_params: Dictionary, the values of which are used to replace path parameters using the keys.
        :return: A string representing the full path url.

        Example:
            path = '/customer/{customer_id}/
            path_params = {'customer_id': 'c1'}
            print(_build_url(path, path_params)
            >> '/customer/c1/'
        """

        # Remove leading slash and force trailing slash
        if path:
            if path[0] == '/':
                path = path[1:]

            if path[-1] != '/' and path.find('?') == -1:
                path += '/'

        url = self.url_root + path
        start = url.find('{')

        while start >= 0:
            end = url.find('}', start)
            replace = url[start:end + 1]
            param = str(path_params.get(replace[1:-1]))
            url = url.replace(replace, param if param else '')
            start = url.find('{')

        return url

    @property
    def url_root(self):
        return self._url_root

    @url_root.setter
    def url_root(self, value):
        # Force trailing slash
        self._url_root = value if value[-1] == '/' else '%s/' % value

    def make_request(self, method, path='', path_params=None, query_params=None, data=None, headers=None,
                     timeout=None, raise_exception=True):
        """
        :param method: HTTP method
        :param path: Appended to the end of _url_root. Supports {param_name} replacement.
        :param path_params: Dictionary, the values of which are used to replace path parameters using the keys.
        :param query_params: Dictionary or bytes to be sent in the query string for the Request.
        :param data: Dictionary, bytes, or file-like object to send in the body of the Request.
        :param headers: Dictionary of HTTP Headers to send with the Request.
        :param timeout: (float or tuple) How long to wait for the server to send data before giving up, as a float,
                        or a (connect timeout, read timeout) tuple.
        :param raise_exception: Raise a GatewayException if the response status_code >= 300.
        :return: Requests Response object
        """

        path_params = path_params if path_params else {}
        url = self._build_url(path, **path_params)

        res = self._requestor.request(
            method,
            url,
            params=query_params,
            data=data,
            headers=headers,
            timeout=timeout if timeout else self._timeout,
            auth=self._auth
        )

        if res.status_code >= 300 and raise_exception:
            raise HttpClientException(response=res)

        return res

    def get(self, path='', path_params=None, query_params=None, headers=None, raise_exception=True):
        return self.make_request('GET', path, path_params, query_params=query_params,
                                 headers=headers, raise_exception=raise_exception)

    def post(self, path='', path_params=None, data=None, headers=None, raise_exception=True):
        return self.make_request('POST', path, path_params, data=data,
                                 headers=headers, raise_exception=raise_exception)

    def put(self, path='', path_params=None, data=None, headers=None, raise_exception=True):
        return self.make_request('PUT', path, path_params, data=data,
                                 headers=headers, raise_exception=raise_exception)

    def patch(self, path='', path_params=None, data=None, headers=None, raise_exception=True):
        return self.make_request('PATCH', path, path_params, data=data,
                                 headers=headers, raise_exception=raise_exception)

    def delete(self, path='', path_params=None, headers=None, raise_exception=True):
        return self.make_request('DELETE', path, path_params,
                                 headers=headers, raise_exception=raise_exception)
