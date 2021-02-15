from requests.adapters import HTTPAdapter
from urllib3.util import parse_url
import re


class DatasnapSessionAdapter(HTTPAdapter):
    def __init__(self, cache, **kwargs):
        self.cache = cache
        super().__init__(**kwargs)

    @staticmethod
    def _get_cache_key(request):
        scheme, auth, host, port, path, query, fragment = parse_url(
            request.url)
        return 'dssession:{}:{}'.format(host, port)

    def add_headers(self, request, **kwargs):
        super().add_headers(request, **kwargs)
        dssession = self.cache.get(self._get_cache_key(request))
        if dssession:
            request.headers['Pragma'] = 'dssession=' + dssession

    def build_response(self, req, resp):
        response = super().build_response(req, resp)
        m = re.search(r'dssession=([^,\s]+)',
                      response.headers.get('Pragma', ''))
        if m:
            self.cache.set(self._get_cache_key(req), m.group(1))
        return response
