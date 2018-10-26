
class RequestContextSerializerMixin(object):
    @property
    def request(self):
        try:
            return self.context.get('request', None)
        except AttributeError:
            return None


class SubdomainSerializerMixin(RequestContextSerializerMixin):
    @property
    def subdomain(self):
        return self.request.parser_context['kwargs']['domain_pk']
