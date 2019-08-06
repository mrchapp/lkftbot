# coding=utf-8
# Copyright 2017 Matt Hart
# Licensed under the Eiffel Forum License 2

from __future__ import unicode_literals, absolute_import, print_function, division

import xmltodict
import requests

from sopel.config.types import StaticSection, ValidatedAttribute, ListAttribute
from sopel.module import rule
api_url = '{}/si/jira.issueviews:issue-xml/{}/{}.xml?field=title&field=status&field=resolution'
browse_url = '{}/browse/{}'
from sopel.logger import get_logger

LOG = get_logger(__name__)


class JiraSection(StaticSection):
    username = ValidatedAttribute('username')
    password = ValidatedAttribute('password')
    base_url = ValidatedAttribute('base_url')
    allowed_channels = ListAttribute('allowed_channels')


def configure(config):
    config.define_section('jira', JiraSection)
    config.jira.configure_setting('username', 'Enter your JIRA username')
    config.jira.configure_setting('password', 'Enter your JIRA password')
    config.jira.configure_setting('base_url', 'Enter your JIRA base (example: https://projects.linaro.org)')


def setup(bot):
    bot.config.define_section('jira', JiraSection)
    if not bot.config.jira.username or not bot.config.jira.password or not bot.config.jira.base_url:
        return


def get_story(story, bot):
    story = story.upper()
    url = api_url.format(bot.config.jira.base_url, story, story)
    http = requests.get(url, auth=(bot.config.jira.username, bot.config.jira.password))
    if http.status_code == 302 or http.status_code == 404:
        return False
    story_url = browse_url.format(bot.config.jira.base_url, story)
    datadict = xmltodict.parse(http.content)
    title = datadict['rss']['channel']['item']['title']
    status = datadict['rss']['channel']['item']['status']['#text']
    resolution = datadict['rss']['channel']['item']['resolution']['#text']
    if datadict:
        return '{} ({}, {}) {}'.format(title, status.upper(), resolution.upper(), story_url)
    return False


@rule('.*(LSS-[0-9]+).*')
@rule('.*(STG-[0-9]+).*')
@rule('.*(KV-[0-9]+).*')
@rule('.*(LAVA-[0-9]+).*')
def story(bot, trigger):
    """Give the JIRA project title"""
    if trigger.sender in bot.config.jira.allowed_channels:
        text = get_story(trigger.group(1), bot)
        if text:
            bot.say(text)
