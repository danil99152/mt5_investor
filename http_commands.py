"""Functions collection for HTTP requests"""
import aiohttp
import settings


async def get(url):
    response = []
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as get_response:
                response = await get_response.json()
    except Exception as e:
        print('Exception in get():', e)
    return response


async def patch(url, data):
    response = []
    try:
        async with aiohttp.ClientSession(headers={"Content-type": "application/json"}) as session:
            async with session.patch(url=url, data=data) as get_response:
                response = await get_response.json()
                if get_response.status != 200:
                    print('PATCH', get_response.status, get_response.reason)
    except Exception as e:
        print('Exception in patch():', e)
    return response


async def post(url, data):
    response = []
    try:
        async with aiohttp.ClientSession(headers={"Content-type": "application/json"}) as session:
            async with session.post(url=url, data=data) as get_response:
                response = await get_response.json()
                if get_response.status != 200:
                    print('POST', get_response.status, get_response.reason)
    except Exception as e:
        print('Exception in post():', e)
    return response


async def get_current_db_record_id():
    url = settings.host + 'last'
    rsp = await get(url)
    if not len(rsp):
        return None
    response = rsp[0]
    return response['id']


async def send_comment(comment):
    if not comment or comment == 'None':
        return
    idx = await get_current_db_record_id()
    if not idx:
        return
    url = settings.host + f'patch/{idx}/'
    await patch(url=url, data={"comment": comment})
