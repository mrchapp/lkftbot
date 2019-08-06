# coding=utf-8
# Copyright 2017 Matt Hart
# Licensed under the Eiffel Forum License 2

import requests
import subprocess

from sopel.config.types import StaticSection, ListAttribute
from sopel.module import interval
from sopel.logger import get_logger

LOG = get_logger(__name__)


class GitTagSection(StaticSection):
    treelist = ListAttribute('treelist')
    allowed_channels = ListAttribute('allowed_channels')


def configure(config):
    config.define_section('git_tag', GitTagSection)
    config.git_tag.configure_setting('treelist', 'Enter your list of trees to monitor ([stable#linux-4.18.y, mainline#master])')


def setup(bot):
    bot.config.define_section('git_tag', GitTagSection)
    if not bot.config.git_tag.treelist:
        return


def bot_say(bot, text):
    text = "[GIT] {}".format(text)
    LOG.info(text)
    for channel in bot.channels:
        if channel in bot.config.git_tag.allowed_channels:
            bot.say(text, channel)


def get_git_tag(text):
    for line in text:
        if line.startswith('VERSION'):
            version = line.split('=')[1].strip()
        if line.startswith('PATCHLEVEL'):
            patchlevel = line.split('=')[1].strip()
        if line.startswith('SUBLEVEL'):
            sublevel = line.split('=')[1].strip()
        if line.startswith('EXTRAVERSION'):
            extraversion = line.split('=')[1].strip()
    return "v{}.{}.{}{}".format(version, patchlevel, sublevel, extraversion)


@interval(180)
def xmlrpc_update(bot):
    if 'git_tag' not in bot.memory:
        bot.memory['git_tag'] = {}
    for tree in bot.config.git_tag.treelist:
        #bot.memory['git_tag']['updating'] = True
        name, url = tree.split('#')
        ls_data = subprocess.check_output(['git', 'ls-remote', url, 'refs/heads/*'])
        ls_data = ls_data.decode('utf-8')
        ls_data = ls_data.strip()
        for head_data in ls_data.split('\n'):
            head_data = head_data.split('\t')
            commit = head_data[0]
            branch = head_data[1]
            branch = branch.replace('refs/heads/', '')
            makefile_url = "{}/plain/Makefile?h={}".format(url, branch)
            http = requests.get(makefile_url)
            if http.status_code == 302 or http.status_code == 404:
                continue
            toplines = http.content.decode('utf-8').split('\n')
            git_tag = get_git_tag(toplines[:6])
            treebranch = "{}#{}".format(name, branch)
            git_describe = "{} ({})".format(git_tag, commit)
            if treebranch in bot.memory['git_tag']:
                if bot.memory['git_tag'][treebranch] != git_describe:
                    bot_say(bot, "{} has new tag {}".format(treebranch, git_describe))
                    bot.memory['git_tag'][treebranch] = git_describe
                else:
                    LOG.debug("{} has not changed tag from {}".format(treebranch, git_describe))
            else:
                LOG.info("no tag record for {}, setting to {}".format(treebranch, git_describe))
                bot.memory['git_tag'][treebranch] = git_describe
