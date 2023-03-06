#!/usr/bin/env python
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache
from urllib.parse import quote
from io import BytesIO
from datasnap import DatasnapTransport, deserialize_table
import httpx
import os
import re

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/server_ip')
async def server_ip():
    return await get_server_ip()


@app.get('/status_loja')
@cache(expire=30)
async def status_loja():
    r = await app.state.client.get(f'{await get_base_url()}/GetStatusLoja/')
    return r.json()['result'][0]


@app.get('/departamentos')
@cache(expire=1800)
async def departamentos():
    return await get_table('/GetDepartamentos/PedMoveis.2017/')


@app.get('/produtos_dept/{dept}')
@cache(expire=60)
async def produtos_dept(dept: int):
    return await get_table(f'/GetProdutosDept/PedMoveis.2017/{dept}/')


@app.get('/produtos_consulta/{q}')
async def produtos_consulta(q: str, response: Response):
    response.headers['Cache-Control'] = 'public, max-age=60'
    return await get_table(f'/GetProdutosConsulta/PedMoveis.2017/{quote(q)}/')


@app.get('/produtos/{q}')
async def produtos(q: str):
    return await get_table(f'/GetProdutos/PedMoveis.2017/{q}/')


@app.get('/abastecimento_estoque')
async def abastecimento_estoque():
    return await get_table('/GetAbastecimentoEstoque/PedMoveis.2017/')


@app.get('/prodt_image/{prod_id}.png')
async def prodt_image(prod_id: int, response: Response):
    response.headers['Cache-Control'] = 'public, max-age=604800'
    tbl = await get_table(f'/GetProdtImage/PedMoveis.2017/{prod_id}/')
    img = BytesIO(tbl['FDBS']['Manager']['TableList'][0]['RowList'][0]['Original']['IMAGEM'])
    return StreamingResponse(img, media_type='image/png',
                             headers={'Content-Disposition': f'inline; filename="{prod_id}.png"'})


async def get_base_url():
    server_ip = await get_server_ip()
    return f'http://{server_ip}:5362/datasnap/rest/TsmPedidosMoveis'


async def get_table(path):
    r = await app.state.client.get(f'{await get_base_url()}{path}')
    return deserialize_table(r.json())


@cache(expire=300, namespace='server_ip')
async def get_server_ip():
    r = await app.state.client.get(
        'http://servidor.shsistemas.net:7077/datasnap/rest/TSM/GetIPAcessoRemoto/CAAND')
    m = re.match(r'ok(.*)', r.json()['result'][0])
    return m.group(1)


@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")

    async def raise_on_4xx_5xx(r):
        r.raise_for_status()

    app.state.client = httpx.AsyncClient(
            mounts={"all://": DatasnapTransport()},
            event_hooks={'response': [raise_on_4xx_5xx]},
            auth=(os.getenv('DATASNAP_USER', ''),
                  os.getenv('DATASNAP_PASS', '')))
