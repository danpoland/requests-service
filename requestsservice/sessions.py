class SessionCache:
    """
    Simple caching mechanism for Request Sessions.
    Do this allows us to keep the Session connection pools open.
    """

    __sessions = {}

    @classmethod
    def get(cls, name):
        return cls.__sessions.get(name)

    @classmethod
    def set(cls, name, session):
        cls.__sessions[name] = session
