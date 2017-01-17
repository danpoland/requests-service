class ServiceException(Exception):
    """
    Basic exception for wrapping Requests Responses into throwable exceptions when the response.status_code is >= 300.
    """

    def __init__(self, response):
        """
        :param response: Requests Response object
        """

        self.response = response
