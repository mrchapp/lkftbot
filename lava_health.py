# coding=utf-8
# Copyright 2017 Matt Hart
# Licensed under the Eiffel Forum License 2

#from __future__ import unicode_literals, absolute_import, print_function, division

import xmltodict
import xmlrpc.client
from urllib.parse import urlparse

from sopel.config.types import StaticSection, ValidatedAttribute
from sopel.module import thread, interval
from sopel.logger import get_logger

LOG = get_logger(__name__)


class LAVASection(StaticSection):
    url = ValidatedAttribute('url')


def configure(config):
    config.define_section('lava', LAVASection)
    config.lava.configure_setting('url', 'Enter your LAVA url (https://lkft.validation.linaro.org)')


def setup(bot):
    bot.config.define_section('lava', LAVASection)
    if not bot.config.lava.url:
        return


def bot_say(bot, text):
    lava_host = urlparse(bot.config.lava.url)
    text = "[LAVA] {}: {}".format(lava_host.hostname, text)
    LOG.info(text)
    for channel in bot.channels:
        bot.say(text, channel)


@interval(120)
def xmlrpc_update(bot):
    if 'lava_health' not in bot.memory:
        bot.memory['lava_health'] = {}
    server = xmlrpc.client.ServerProxy("{}/RPC2".format(bot.config.lava.url))
    all_devices = server.scheduler.all_devices()
    for device in all_devices:
        hostname = device[0]
        device_info = server.scheduler.devices.show(hostname)
        health = device_info['health']
        if health == 'Unknown' or health == 'Maintenance':
            continue
        if hostname in bot.memory['lava_health']:
            if bot.memory['lava_health'][hostname] != health:
                bot_say(bot, "device {} health has changed to {}".format(hostname, health))
                bot.memory['lava_health'][hostname] = health
            else:
                LOG.debug("device {} health has not changed from {}".format(hostname, health))
        else:
            LOG.info("no health record for {}, setting to {}".format(hostname, health))
            bot.memory['lava_health'][hostname] = health
