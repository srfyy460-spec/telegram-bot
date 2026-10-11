import telebot

bot = telebot.TeleBot("8859824190:AAHbdkUd6lc6PSmu8fJQGVJ8mFc9PaIzCZA")


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "خوش اومدی عزیزم ❤️"
    )


bot.infinity_polling()
