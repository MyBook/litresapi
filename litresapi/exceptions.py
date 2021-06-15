class LitresAPIException(Exception):
    def __init__(self, message, response):
        self.message = message
        self.response = response
        super().__init__(message, response)

    def __str__(self):
        return '%s -> %s' % (self.message, self.response.text)
