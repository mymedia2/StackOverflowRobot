#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import telebot
import stackoverflow
import utils

_STANDARD_FILTER = "!.o3-EiGV6QCtOtVthuVD9Ast*ggGm(2Gu-FVcuc3)wKEZeWxS*"
_EXTENDED_FILTER = "!)E5bKOFZNVzP4(Mqt.ujYtZ_gVGHhlaUVM1UJbYkJo3j5JE1M"

bot = telebot.TeleBot(os.environ['BOT_TOKEN'])
so = stackoverflow.StackOverflow()

@bot.message_handler(commands=['start', 'help'])
def help(message):
    bot.send_message(message.chat.id, "Hello!")

@bot.callback_query_handler(func=lambda l: True)
def callbacks(call):
    bot.answer_callback_query(call.id,
        "Not implemented yet \N{disappointed but relieved face}")

@bot.message_handler()
def search(message):
    data = so.request('search/advanced', sort='relevance', order='desc',
                      pagesize=1, site='stackoverflow', q=message.text,
                      filter=_STANDARD_FILTER)
    if len(data['items']) == 0:
        bot.send_message(message.chat.id, "Not found \N{disappointed face}")
    else:
        question, answers = data['items'][0], data['items'][0]['answers']
        bot.send_message(message.chat.id, parse_mode='html',
                         text=utils.construct_message(question),
                         reply_markup=utils.construct_keyboard(question),
                         disable_web_page_preview=True)

        answers.sort(key=lambda a: (a['is_accepted'], a['score']), reverse=True)
        if len(answers) != 0:
            bot.send_message(message.chat.id, parse_mode='html',
                             text=utils.construct_message(answers[0]),
                             reply_markup=utils.construct_keyboard(answers[0]),
                             disable_web_page_preview=True)

        keyboard = telebot.types.InlineKeyboardMarkup()
        if len(answers) == 0:
            text = "No answers \N{pensive face}"
        elif len(answers) == 1:
            text = "No more answers \N{smirking face}"
        else:
            text = "{} answers in total\N{smiling face with sunglasses}" \
                   .format(question['answer_count'])
            keyboard.add(telebot.types.InlineKeyboardButton("\u25b6 Next answer",
                         callback_data="not_implemented"))
        keyboard.add(telebot.types.InlineKeyboardButton("\u27a1 Next question",
                     callback_data="not_implemented"))
        bot.send_message(message.chat.id, text, reply_markup=keyboard)

bot.polling(none_stop=True, timeout=50)
