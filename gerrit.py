# coding=utf-8
# Copyright 2017 Matt Hart
# Licensed under the Eiffel Forum License 2

from __future__ import unicode_literals, absolute_import, print_function, division

import feedparser
import json
import requests

from sopel.module import rule
from sopel.config.types import StaticSection, ValidatedAttribute
api_url = '{}/changes/{}'
browse_url = '{}/#/c/{}'
from sopel.logger import get_logger

LOG = get_logger(__name__)

class GerritSection(StaticSection):
    base_url = ValidatedAttribute('base_url')


def configure(config):
    config.define_section('gerrit', GerritSection)
    config.gerrit.configure_setting('base_url', 'Enter your Gerrit base (example: https://review.linaro.org)')


def setup(bot):
    bot.config.define_section('gerrit', GerritSection)
    if not bot.config.gerrit.base_url:
        return


def get_change(change, bot):
    url = api_url.format(bot.config.gerrit.base_url, change)
    http = requests.get(url)
    if http.status_code == 302 or http.status_code == 404:
        return False
    data = http.content.decode('utf-8').replace(")]}'",'')
    changedata = json.loads(data)
    if changedata:
        return '[REVIEW] {} (STATUS: {}) {}'.format(changedata['subject'], changedata['status'], browse_url.format(bot.config.gerrit.base_url, change))
    return False


@rule('.*review.*([0-9]{5}).*')
@rule('.*review.*([0-9]{6}).*')
@rule('.*([0-9]{5}).*review.*')
@rule('.*([0-9]{6}).*review.*')
def story(bot, trigger):
    text = get_change(trigger.group(1), bot)
    if text:
        bot.say(text)
