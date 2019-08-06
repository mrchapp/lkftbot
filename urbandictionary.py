# coding=utf-8
# Copyright 2017 Matt Hart
# Licensed under the Eiffel Forum License 2

from __future__ import unicode_literals, absolute_import, print_function, division

import json
import requests

from sopel import web
from sopel.module import commands
base_url = 'http://api.urbandictionary.com/v0/define?term={}'
from sopel.config.types import StaticSection, ListAttribute

class UrbanDictionarySection(StaticSection):
    allowed_channels = ListAttribute('allowed_channels')

def setup(bot):
    bot.config.define_section('urbandictionary', UrbanDictionarySection)

def get_def(query):
    url = base_url.format(query)
    http = requests.get(url)
    if http.status_code == 302 or http.status_code == 404:
        return False
    data = http.content.decode('utf-8')
    defdata = json.loads(data)
    deflist = defdata['list']
    if not deflist:
        return "UrbanDictionary: Sorry, couldn't find anything for '{}'".format(query)
    deflines = deflist[0]['definition']
    defintion = deflines.splitlines()[0]
    if defintion:
        return 'UrbanDictionary: [{}] {}'.format(query, defintion)
    return False

@commands('slang')
def story(bot, trigger):
    if trigger.sender in bot.config.jira.allowed_channels:
        """Give the JIRA project title"""
        text = get_def(trigger.group(2))
        if text:
            bot.say(text)
