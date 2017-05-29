#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import telebot
import stackoverflow
import utils

_STANDARD_FILTER = "!*i5nbupzVkd_nFQ_R3K24wS_Ib*wHM4j*K*R(VlvYEcL57*XBFrX*Dy-.zQW_5V9GMDr_."

bot = telebot.TeleBot(os.environ['BOT_TOKEN'])
so = stackoverflow.StackOverflow(_STANDARD_FILTER)

@bot.message_handler(commands=['start', 'help'])
def help(message):
    bot.send_message(message.chat.id, "Hello!")

@bot.callback_query_handler(func=lambda l: True)
def callbacks(call):
    bot.answer_callback_query(call.id,
        "Not implemented yet \N{disappointed but relieved face}")

@bot.inline_handler(func=lambda l: True)
def inline_search(query):
    data = so.request('search/excerpts', sort='relevance', order='desc',
                         pagesize=10, site='stackoverflow', q=query.query)
    if len(data['items']) == 0:
        # TODO: ...
        bot.answer_inline_query(query.id, [])
        return

    questions = (p['question_id'] for p in data['items']
                 if p['item_type'] == 'question')
    questions = so.request('questions/{ids}', ids=';'.join(map(str, questions)),
                           site='stackoverflow')
    questions = {p['question_id']: p for p in questions['items']}

    answers = (p['answer_id'] for p in data['items']
               if p['item_type'] == 'answer')
    answers = so.request('answers/' + ';'.join(map(str, answers)),
                         site='stackoverflow')
    answers = {p['answer_id']: p for p in answers['items']}

    results = list()
    for el in data['items']:
        if el['item_type'] == 'question':
            post = questions[el['question_id']]
        else:
            post = answers[el['answer_id']]
        post['post_id'] = post.get('question_id') or post.get('answer_id')
        post['post_type'] = el['item_type']

        results.append(telebot.types.InlineQueryResultArticle(
            str(post['post_id']), utils.remove_tags(post['title']),
            telebot.types.InputTextMessageContent(
                utils.construct_message(post), parse_mode='html',
                disable_web_page_preview=True),
            reply_markup=utils.construct_keyboard(post), url=post['link'],
            description=utils.truncate_line(
                utils.remove_tags(post['body']), 100)))

    bot.answer_inline_query(query.id, results, cache_time=1)

@bot.message_handler()
def normal_search(message):
    q_data = so.request('search/advanced', sort='relevance', order='desc',
                        pagesize=1, site='stackoverflow', q=message.text)
    if len(q_data['items']) == 0:
        bot.send_message(message.chat.id, "Not found \N{disappointed face}")
        return

    question = q_data['items'][0]
    question['post_type'] = 'question'
    bot.send_message(message.chat.id, parse_mode='html',
                     text=utils.construct_message(question),
                     reply_markup=utils.construct_keyboard(question),
                     disable_web_page_preview=True)

    a_data = so.request('questions/{ids}/answers', ids=question['question_id'],
                        sort='votes', order='desc', pagesize=1,
                        site='stackoverflow')
    if len(a_data['items']) != 0:
        answer = a_data['items'][0]
        answer['post_type'] = 'answer'
        bot.send_message(message.chat.id, parse_mode='html',
                         text=utils.construct_message(answer),
                         reply_markup=utils.construct_keyboard(answer),
                         disable_web_page_preview=True)

    keyboard = telebot.types.InlineKeyboardMarkup()
    if len(a_data['items']) == 0:
        summary = "No answers \N{pensive face}"
    elif not a_data['has_more']:
        summary = "No more answers \N{smirking face}"
    else:
        summary = "{} answers in total\N{smiling face with sunglasses}" \
                  .format(question['answer_count'])
        keyboard.add(telebot.types.InlineKeyboardButton("\u25b6 Next answer",
                     callback_data="not_implemented"))
    if q_data['has_more']:
        keyboard.add(telebot.types.InlineKeyboardButton("\u27a1 Next question",
                     callback_data="not_implemented"))

    bot.send_message(message.chat.id, summary, reply_markup=keyboard)

bot.polling(timeout=50)
