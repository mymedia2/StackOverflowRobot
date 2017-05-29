#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import html.parser
import json
import re
import telebot

class _HtmlSimplifying(html.parser.HTMLParser):

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.result = list()
        self._tag_context = None
        self._list_context = list()

    def handle_starttag(self, tag, attrs):
        if self._tag_context:
            return
        attrs = dict(attrs)
        if tag == 'kbd':
            tag = 'code'
        if tag == 'a' and 'href' in attrs:
            self.result.append('<a href="{}">'.format(attrs['href']))
            self._tag_context = 'a'
        if tag in ['b', 'strong', 'i', 'em', 'code', 'pre']:
            self.result.append('<{}>'.format(tag))
            self._tag_context = tag
        if tag == 'br':
            self.result.append('\n')
        if tag == 'blockquote':
            self.result.append('&gt;')
        if tag in ['ol', 'ul']:
            self._list_context.append({'tag': tag, 'counter': 0})
        if tag == 'li' and len(self._list_context) != 0:
            self._list_context[-1]['counter'] += 1
            if self._list_context[-1]['tag'] == 'ol':
                num = str(self._list_context[-1]['counter'])
                self.result.append(num + ". ")
            if self._list_context[-1]['tag'] == 'ul':
                self.result.append("\N{bullet} ")
        if tag == 'img' and 'src' in attrs and 'alt' in attrs:
            self.result.append('<a href="{}">{}</a>'
                               .format(attrs['src'], attrs['alt']))

    def handle_endtag(self, tag):
        if tag == 'kbd':
            tag = 'code'
        if tag in ['a', 'b', 'strong', 'i', 'em', 'code', 'pre'] and \
                self._tag_context == tag:
            self.result.append('</{}>'.format(tag))
            self._tag_context = None
        if tag in ['ol', 'ul'] and len(self._list_context) != 0 and \
                self._list_context[-1]['tag'] == tag:
            self._list_context.pop()
        if tag in ['p', 'li', 'pre'] and not self.result[-1].isspace():
            self.result.append('\n\n')

    def handle_data(self, text):
        if self._tag_context == 'pre':
            text = text.rstrip()
        else:
            text = text.replace('\n', '')
        if not self._tag_context:
            # FIXME: the last substitution breaks emails
            text = text.replace('#', '#\N{word joiner}') \
                       .replace('@', '@\N{word joiner}')
        self.result.append(text.replace('&', '&amp;').replace('"', '&quot;')
                           .replace('<', '&lt;').replace('>', '&gt;'))

    def close(self):
        super().close()
        self.result = "".join(self.result)

def simplify_html(s):
    """Make a real HTML text compatible with Telegram's pseudo-HTML"""

    parser = _HtmlSimplifying()
    parser.feed(s)
    parser.close()
    print(repr(s))
    print(repr(parser.result))
    return parser.result

_truncate_pattern = re.compile(r'\W*\w+')
def truncate_line(s, length, suffix="...", norm=len):
    """Shrink the given text to to the specified length.

    If the text is truncated, then the suffix is appended. Words can't be split.
    """

    if norm(s) <= length:
        return s
    if length < norm(suffix):
        raise AttributeError("length must be greater than suffix size")

    result = list()
    for word in _truncate_pattern.finditer(s):
        if sum(map(norm, result)) + norm(word.group()) + norm(suffix) > length:
            break
        result.append(word.group())

    return "".join(result) + suffix

_clean_pattern, _compress_pattern = re.compile(r'<.*?>'), re.compile(r'&.*?;')
def clear_length(s):
    """Compute length of the given string without tags and entities"""

    return len(_compress_pattern.sub('%', _clean_pattern.sub('', s)))

_MAX_POST_LENGTH = 4096
_QUESTION_HEADER_TEMPLATE = \
    """<b>Question</b> <a href="{link}">{title}</a>\n\n"""
_QUESTION_FOOTER_TEMPLATE = "\n\ntags: {tag_list}\n" + \
    """asked {creation_date} by <a href="{owner_link}">{owner_name}</a>"""
_ANSWER_HEADER_TEMPLATE = \
    """{accepted_mark}<b>Answer</b> to <a href="{link}">{title}</a>\n\n"""
_ANSWER_FOOTER_TEMPLATE = "\n\n" + \
    """answered {creation_date} by <a href="{owner_link}">{owner_name}</a>"""

def construct_message(post):
    """Build a text of a Telegram message."""

    creation_date = datetime.date.fromtimestamp(post['creation_date'])
    current_date = datetime.date.today()
    if (current_date - creation_date).days == 0:
        creation_date = "today"
    elif (current_date - creation_date).days == 1:
        creation_date = "yesterday"
    elif creation_date.year == current_date.year:
        if creation_date.day < 10:
            creation_date = creation_date.strftime("%b%e")
        else:
            creation_date = creation_date.strftime("%b %d")
    else:
        if creation_date.day < 10:
            creation_date = creation_date.strftime("%b%e '%y")
        else:
            creation_date = creation_date.strftime("%b %d '%y")
    del current_date

    if 'tags' in post:
        tag_list = ", ".join(["[<b>" + t + "</b>]" for t in post['tags']])
    accepted_mark = ""
    if 'is_accepted' in post:
        accepted_mark = "\N{white heavy check mark} "
    link, title = post['link'], post['title']
    owner_link, owner_name = post['owner']['link'], post['owner']['display_name']

    if 'answer_id' not in post:  # then this post is a question
        top = _QUESTION_HEADER_TEMPLATE.format(**locals())
        bottom = _QUESTION_FOOTER_TEMPLATE.format(**locals())
    else:
        top = _ANSWER_HEADER_TEMPLATE.format(**locals())
        bottom = _ANSWER_FOOTER_TEMPLATE.format(**locals())
    middle = truncate_line(simplify_html(post['body']).strip(),
                           _MAX_POST_LENGTH - clear_length(top) -
                           clear_length(bottom), norm=clear_length)
    return top + middle + bottom

def construct_keyboard(post):
    up_votes = "0"
    if post['up_vote_count'] != 0:
        up_votes = "\N{plus sign}" + str(post['up_vote_count'])
    down_votes = "0"
    if post['down_vote_count'] != 0:
        down_votes = "\N{minus sign}" + str(post['down_vote_count'])
    buttons = [
        telebot.types.InlineKeyboardButton(callback_data="not_implemented",
            text="\N{up-pointing small red triangle} " + up_votes),
        telebot.types.InlineKeyboardButton(callback_data="not_implemented",
            text="\N{down-pointing small red triangle} " + down_votes),
    ]
    if 'favorite_count' in post:
        buttons.append(
            telebot.types.InlineKeyboardButton(callback_data="not_implemented",
                text="\N{white medium star} " + str(post['favorite_count'])))
    result = telebot.types.InlineKeyboardMarkup()
    result.add(*buttons)
    return result
