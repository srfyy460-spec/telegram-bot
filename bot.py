import telebot

bot = telebot.TeleBot("توکن_ربات_اینجا")


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "خوش اومدی عزیزم ❤️"
    )


bot.infinity_polling()
