from adbs import TableDeserializer
import httpx
from io import BytesIO
from zlib import decompress
from base64 import b64decode
import re


class DatasnapTransport(httpx.AsyncHTTPTransport):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._dssession = {}

    async def handle_async_request(
        self,
        request: httpx.Request,
    ) -> httpx.Response:
        key = f'{request.url.host}:{request.url.port}'
        dssession = self._dssession.get(key)
        if dssession:
            request.headers['Pragma'] = 'dssession=' + dssession

        response = await super().handle_async_request(request)

        m = re.search(r'dssession=([^,\s]+)',
                      response.headers.get('Pragma', ''))
        if m:
            self._dssession[key] = m.group(1)

        return response


def deserialize_table(json):
    fvalue = (json['result'][0]['fields']['FDataSets']['fields']
              ['FMembers'][0]['fields']['FJsonValue']['fields']['FValue'])
    f = BytesIO(decompress(b64decode(fvalue)))
    return TableDeserializer(f).load()
