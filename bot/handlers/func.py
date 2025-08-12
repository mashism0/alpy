from aiogram.types import Message
from aiogram import Bot

# Храним последнее временное сообщение в памяти на пользователя (по user_id)
temp_messages: dict[int, int] = {}

async def send_temp_message(bot: Bot, message: Message, text: str) -> int:
    """
    Отправляет сообщение и сохраняет его message_id для последующего удаления.
    Возвращает message_id этого сообщения.
    """
    sent = await bot.send_message(chat_id=message.chat.id, text=text)
    temp_messages[message.from_user.id] = sent.message_id
    return sent.message_id

async def delete_temp_message(bot: Bot, message: Message):
    msg_id = temp_messages.pop(message.from_user.id, None)
    if msg_id:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception as e:
            print(f"❌ Не удалось удалить временное сообщение: {e}")