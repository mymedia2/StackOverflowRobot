#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import telebot
import stackoverflow
import private_search
import utils

_STANDARD_FILTER = "!8463uz9IO9g-pvq5plHxzY3C8l9vpUT0hxO81BfFRHdrLvA4aSNsX2WEshLSfzNGNhF"

bot = telebot.TeleBot(os.environ['BOT_TOKEN'])
so = stackoverflow.StackOverflow(_STANDARD_FILTER)

@bot.message_handler(commands=['start', 'help'])
def help(message):
    bot.send_message(message.chat.id, """\
Hello! I was made to simplify search for questions and answers on \
stackoverflow.com and other Stack Exchange sites. I do the finding on the main \
SO by default, but you can tell me to search on another site by typing its \
name at the beginning of your query.""", disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda l: l.data == 'not_implemented')
def callbacks(call):
    bot.answer_callback_query(call.id,
        "Not implemented yet \N{disappointed but relieved face}")

@bot.inline_handler(func=lambda l: True)
def inline_search(iquery):
    area, query = utils.detect_target_site(iquery.query)
    print(area, query)
    data = so.request('search/excerpts', q=query, sort='relevance',
                      order='desc', pagesize=10, site=area)
    if len(data['items']) == 0:
        # TODO: ...
        bot.answer_inline_query(iquery.id, [])
        return

    questions = [p['question_id'] for p in data['items']
                 if p['item_type'] == 'question']
    if questions:
        questions = so.request('questions/{ids}', site=area,
                               ids=';'.join(map(str, questions)))
        questions = {p['question_id']: p for p in questions['items']}

    answers = [p['answer_id'] for p in data['items']
               if p['item_type'] == 'answer']
    if answers:
        answers = so.request('answers/{ids}', ids=';'.join(map(str, answers)),
                             site=area)
        answers = {p['answer_id']: p for p in answers['items']}

    results = list()
    for el in data['items']:
        if el['item_type'] == 'question':
            post = questions[el['question_id']]
        else:
            post = answers[el['answer_id']]
        post['post_id'] = post.get('answer_id') or post.get('question_id')
        post['post_type'] = el['item_type']

        if post['post_type'] == 'question':
            if not post['is_answered']:
                preview = 'https://i.stack.imgur.com/h3lUT.png'
            else:
                preview = 'https://i.stack.imgur.com/LEUnx.png'
        else:
            if not post['is_accepted']:
                preview = 'https://i.stack.imgur.com/QaNW7.png'
            else:
                preview = 'https://i.stack.imgur.com/qzQHK.png'

        results.append(telebot.types.InlineQueryResultArticle(
            str(post['post_id']), utils.remove_tags(post['title']),
            telebot.types.InputTextMessageContent(
                utils.construct_message(post), parse_mode='html',
                disable_web_page_preview=True),
            reply_markup=utils.construct_keyboard(post), url=post['link'],
            thumb_url=preview, thumb_width=48, thumb_height=48,
            description=utils.truncate_line(
                utils.remove_tags(post['body']), 100)))

    bot.answer_inline_query(iquery.id, results, cache_time=1)

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
    area, query = utils.detect_target_site(message.text)
    print(area, query)
    paginator = private_search.SearchPaginator(message.chat.id, query, area)
    private_search.show_search_result(bot, so, paginator)
    paginator.save()

bot.polling(timeout=50)
