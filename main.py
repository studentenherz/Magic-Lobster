import asyncio
from asyncio import tasks
from subprocess import call
from telebot.async_telebot import AsyncTeleBot
from credentials import BOT_TOKEN
from telebot import types
from jamendo_requests import create_session, close_session, search_tracks, get_album, get_album_tracks

bot = AsyncTeleBot(BOT_TOKEN)

limit = 6
inline_limit = 20


@bot.message_handler(commands=['help'])
async def bot_handle_help(message):
	await bot.send_message(message.chat.id, 'Use /tracks command to search for free music on <a href="https://www.jamendo.com/">Jamendo</a>. Use /tracks <code>name</code> to filter your search.', disable_web_page_preview=True, parse_mode='HTML')
	

@bot.message_handler(commands=['start'])
async def bot_handle_start(message):
	await bot.send_message(message.chat.id, f'Wellcome {message.from_user.first_name}, bot is still in developement, but you can already start giving feedbak at @magiclobsters.', disable_web_page_preview=True)
	await bot.send_chat_action(message.chat.id, 'typing')
	await bot_handle_help(message)

async def send_album(chat_id, album_id):
	album = await get_album(album_id)
	keyboard = types.InlineKeyboardMarkup()
	keyboard.row(types.InlineKeyboardButton(f"See tracks", callback_data=f"s{album['id']}"), types.InlineKeyboardButton('Listen on Jamendo', url=album['shorturl']))
	await bot.send_photo(chat_id, album['image'], caption=f"{album['name']}\nArtist: {album['artist_name']}\nRelease date: {album['releasedate']}", reply_markup=keyboard)

@bot.message_handler(commands=['tracks'])
async def bot_handle_send(message):
	command = message.text.split(' ', 1)
	name = None
	if len(command) > 1:
		name = command[1]
	list, has_next = await search_tracks(0, limit, name)
	if len(list) == 0:
		await bot.send_message(message.chat.id, 'No match found :(')
	elif len(list) == 1:
		track = list[0]
		keyboard = types.InlineKeyboardMarkup()
		keyboard.row(types.InlineKeyboardButton(f"Donwload", callback_data=f"t{track['id']}"), types.InlineKeyboardButton('Listen on Jamendo', url=track['shorturl']))
		keyboard.row(types.InlineKeyboardButton(f"See album", callback_data=f"a{track['album_id']}"), types.InlineKeyboardButton('See artist', callback_data=f"r{track['artist_id']}"))
		await bot.send_photo(message.chat.id, track['image'], caption=f"Name: {track['name']}\nArtist: {track['artist_name']}\nAlbum: {track['album_name']}\nRelease date: {track['releasedate']}", reply_markup=keyboard)
		
	else:
		keyboard = types.InlineKeyboardMarkup()
		for track in list:
			keyboard.row(types.InlineKeyboardButton(f"{track['artist_name']}-{track['name']}", callback_data=f"t{track['id']}"))
		if has_next:
			keyboard.row(types.InlineKeyboardButton('Next =>', callback_data=f'n{limit}{"_" + name if name else ""}'))
		text = "Searching traks " 
		if name:
			text += f"with <i>{name}</i> in the name "
		text += f"[1-{len(list)}]"
		await bot.send_message(message.chat.id, f'<a href="{list[0]["image"]}">&#x200b;</a> {text}', reply_markup=keyboard, parse_mode='HTML')

@bot.callback_query_handler(lambda q: True)
async def bot_handle_callbacks(call):
	if call.data:
		action = call.data[0]
		data = call.data[1:]
		if action == 't':
			send_audio = asyncio.create_task(bot.send_audio(call.message.chat.id, f"https://mp3d.jamendo.com/download/track/{data}/mp32/"))
			await bot.answer_callback_query(call.id, 'Sending Audio...')
			await send_audio
		elif action == 'n':
			name = None
			data_split = data.split('_', 1)
			if len(data_split) > 1:
				name = data_split[1]
			offset = int(data_split[0])
			list, has_next = await search_tracks(offset, limit, name)

			keyboard = types.InlineKeyboardMarkup()
			for track in list:
				keyboard.row(types.InlineKeyboardButton(f"{track['artist_name']}-{track['name']}", callback_data=f"t{track['id']}"))
			
			next_button = types.InlineKeyboardButton('Next =>', callback_data=f'n{offset + limit}{"_" + name if name else ""}')
			if offset >= limit:
				prev_button = types.InlineKeyboardButton('<= Previous', callback_data=f'n{offset - limit}{"_" + name if name else ""}')
				if has_next:
					keyboard.row(prev_button, next_button)
				else:
					keyboard.row(prev_button)
			elif has_next:
				keyboard.row(next_button)

			text = "Searching traks " 
			if name:
				text += f"with <i>{name}</i> in the name "
			text += f"[{offset + 1}-{offset + len(list)}]"

			await bot.edit_message_text(f'<a href="{list[0]["image"]}">&#x200b;</a>{text}', call.message.chat.id, call.message.id, reply_markup=keyboard, parse_mode='HTML')
		elif action == 'a':
			album_id = int(data)
			task = asyncio.create_task(send_album(call.message.chat.id, album_id))
			await bot.answer_callback_query(call.id, 'Sending album...')
			await task
		elif action == 's':
			album_id = int(data)
			list = await get_album_tracks(album_id)
			keyboard = types.InlineKeyboardMarkup()
			for track in list:
				keyboard.row(types.InlineKeyboardButton(f"{track['position']}. {track['name']}", callback_data=f"t{track['id']}"))
			
			keyboard.row(types.InlineKeyboardButton(f"<= Back", callback_data=f"b{album_id}_a"))
			await bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=keyboard)
			await bot.answer_callback_query(call.id)
		elif action == 'b':
			data_split = data.split('_', 1)
			type = data_split[1]
			if type == 'a':
				album = await get_album(data_split[0])
				keyboard = types.InlineKeyboardMarkup()
				keyboard.row(types.InlineKeyboardButton(f"See tracks", callback_data=f"s{album['id']}"), types.InlineKeyboardButton('Listen on Jamendo', url=album['shorturl']))
				await bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=keyboard)
				await bot.answer_callback_query(call.id)
		else:
			await bot.answer_callback_query(call.id, 'Still not implemented, be patient')
			
@bot.inline_handler(lambda q : True)
async def bot_handle_inline_queries(q):
	offset = 0 if q.offset == '' else int(q.offset)
	
	list, has_next = await search_tracks(offset, inline_limit, q.query)
	res = []
	for track in list:
		res.append(types.InlineQueryResultAudio(f"t{track['id']}", track['audio'], track['name'], audio_duration=track['duration'], performer=track['artist_name']))
	await bot.answer_inline_query(q.id, res, next_offset= str(offset + inline_limit) if has_next else None )

async def main():
	await create_session()
	await bot._process_polling(non_stop=True) # infinity polling
	await close_session()


if __name__ == '__main__':
	asyncio.run(main())
	# bot.polling()