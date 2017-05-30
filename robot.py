#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import telebot
import stackoverflow
import private_search
import utils

_STANDARD_FILTER = "!*i5nbupzVkd_nFQ_R3K24wS_Ib*wHM4j*K*R(VlvYEcL57*XBFrX*Dy-.zQW_5V9GMDr_."

bot = telebot.TeleBot(os.environ['BOT_TOKEN'])
so = stackoverflow.StackOverflow(_STANDARD_FILTER)

@bot.message_handler(commands=['start', 'help'])
def help(message):
    bot.send_message(message.chat.id, "Hello!")

@bot.callback_query_handler(func=lambda l: l.data == 'not_implemented')
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

    questions = [p['question_id'] for p in data['items']
                 if p['item_type'] == 'question']
    if questions:
        questions = so.request('questions/{ids}',
                               ids=';'.join(map(str, questions)),
                               site='stackoverflow')
        questions = {p['question_id']: p for p in questions['items']}

    answers = [p['answer_id'] for p in data['items']
               if p['item_type'] == 'answer']
    if answers:
        answers = so.request('answers/{ids}', ids=';'.join(map(str, answers)),
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

@bot.callback_query_handler(func=lambda l: l.data.startswith('next_question:'))
def next_question(call):
    paginator = private_search.SearchPaginator.goto_next_question(call.data)
    private_search.show_search_result(bot, so, paginator)
    paginator.save()
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda l: l.data.startswith('next_answer:'))
def next_answer(call):
    paginator = private_search.SearchPaginator.goto_next_answer(call.data)
    private_search.show_answer_result(bot, so, paginator)
    paginator.save()
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except telebot.apihelper.ApiException:
        pass
    bot.answer_callback_query(call.id)

@bot.message_handler()
def normal_search(message):
    paginator = private_search.SearchPaginator(message.chat.id, message.text)
    private_search.show_search_result(bot, so, paginator)
    paginator.save()

bot.polling(timeout=50)
