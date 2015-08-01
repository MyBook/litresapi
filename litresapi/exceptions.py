# coding: utf-8
class LitresAPIException(Exception):
    def __init__(self, message, response):
        self.message = message
        self.response = response

    def __str__(self):
        return u'%s -> %s' % (self.message, self.response.text)
