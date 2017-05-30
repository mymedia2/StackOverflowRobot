#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import datetime
import os
import shelve
import telebot
import utils

class SearchPaginator:
    def __init__(self, target_chat_id, query_string):
        self._data = base64.urlsafe_b64encode(os.urandom(12))[:-1].decode()
        self.target_chat_id = target_chat_id
        self.query_string = query_string
        self.question_number = 1
        self.answer_number = 1
        self.question_id = None
        self.answers_count = None
        self.has_more_questions = None
        self.last_activity_time = datetime.datetime.utcnow()

    @property
    def question_callback(self):
        return 'next_question:' + self._data

    @property
    def answer_callback(self):
        return 'next_answer:' + self._data

    @staticmethod
    def from_callback(data):
        action, sep, data = data.partition(':')
        with shelve.open('paginators', 'r') as db:
            return db[data]

    def save(self):
        with shelve.open('paginators', 'c') as db:
            db[self._data] = self

    @classmethod
    def goto_next_question(cls, data):
        p = cls.from_callback(data)
        p.question_number += 1
        p.answer_number = 1
        p.last_activity_time = datetime.datetime.utcnow()
        return p

    @classmethod
    def goto_next_answer(cls, data):
        p = cls.from_callback(data)
        p.answer_number += 1
        p.last_activity_time = datetime.datetime.utcnow()
        return p


def show_search_result(bot, so, paginator):
    q_data = so.request('search/advanced', q=paginator.query_string,
                        sort='relevance', order='desc', site='stackoverflow',
                        page=paginator.question_number, pagesize=1)
    paginator.has_more_questions = q_data['has_more']
    if len(q_data['items']) == 0:
        bot.send_message(target_chat_id, "Not found \N{disappointed face}")
        return

    question = q_data['items'][0]
    question['post_type'] = 'question'
    bot.send_message(paginator.target_chat_id, parse_mode='html',
                     text=utils.construct_message(question),
                     reply_markup=utils.construct_keyboard(question),
                     disable_web_page_preview=True)

    paginator.question_id = question['question_id']
    paginator.answers_count = question['answer_count']
    show_answer_result(bot, so, paginator)

def show_answer_result(bot, so, paginator):
    a_data = so.request('questions/{ids}/answers', ids=paginator.question_id,
                        sort='votes', order='desc', site='stackoverflow',
                        page=paginator.answer_number, pagesize=1)
    if len(a_data['items']) != 0:
        answer = a_data['items'][0]
        answer['post_type'] = 'answer'
        bot.send_message(paginator.target_chat_id, parse_mode='html',
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
                  .format(paginator.answers_count)
        keyboard.add(telebot.types.InlineKeyboardButton("\u25b6 Next answer",
                     callback_data=paginator.answer_callback))
    if paginator.has_more_questions:
        keyboard.add(telebot.types.InlineKeyboardButton("\u27a1 Next question",
                     callback_data=paginator.question_callback))
    bot.send_message(paginator.target_chat_id, summary, reply_markup=keyboard)
