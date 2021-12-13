import aiohttp
import asyncio
from credentials import CLIENT_ID

async def create_session():
	global session
	session = aiohttp.ClientSession()

async def close_session():
	await session.close()

async def search_tracks(offset = 0, limit = 10, name = None):
	params = {'client_id': CLIENT_ID, 'format': 'json', 'offset' : offset, 'imagesize': 600, 'limit' : limit}
	if name:
		if len(name) > 0:
			params['name'] = name
	async with session.get('https://api.jamendo.com/v3.0/tracks/', params=params) as response:
		if response.status == 200:
			json = await response.json()

			return json['results'], 'next' in json['headers']

async def search_albums(offset = 0, limit = 10, name = None):
	params = {'client_id': CLIENT_ID, 'format': 'json', 'offset' : offset, 'imagesize': 600, 'limit' : limit}
	if name:
		params['name'] = name
	async with session.get('https://api.jamendo.com/v3.0/albums/', params=params) as response:
		if response.status == 200:
			json = await response.json()

			return json['results'], 'next' in json['headers']

async def get_album(id):
	params = {'client_id': CLIENT_ID, 'format': 'json', 'id': id, 'imagesize': 600}
	async with session.get('https://api.jamendo.com/v3.0/albums/', params=params) as response:
		if response.status == 200:
			json = await response.json()

			return json['results'][0]

async def get_album_tracks(id):
	params = {'client_id': CLIENT_ID, 'format': 'json', 'id': id}
	async with session.get('https://api.jamendo.com/v3.0/albums/tracks/', params=params) as response:
		if response.status == 200:
			json = await response.json()

			return json['results'][0]['tracks']

if __name__ == '__main__':
	pass
