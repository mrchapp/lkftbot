# coding=utf-8
# Copyright 2017 Matt Hart
# Licensed under the Eiffel Forum License 2

import requests
import subprocess
import sys

from sopel.config.types import StaticSection, ListAttribute
from sopel.module import interval
from sopel.logger import get_logger

LOG = get_logger(__name__)


class GitTagSection(StaticSection):
    treelist = ListAttribute("treelist")
    allowed_channels = ListAttribute("allowed_channels")
    ignore_branches = ListAttribute("ignore_branches")


def configure(config):
    config.define_section("git_tag", GitTagSection)
    config.git_tag.configure_setting(
        "treelist",
        "Enter your list of trees to monitor ([stable#linux-4.18.y, mainline#master])",
    )


def setup(bot):
    bot.config.define_section("git_tag", GitTagSection)
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
        if line.startswith("VERSION"):
            version = line.split("=")[1].strip()
        if line.startswith("PATCHLEVEL"):
            patchlevel = line.split("=")[1].strip()
        if line.startswith("SUBLEVEL"):
            sublevel = line.split("=")[1].strip()
        if line.startswith("EXTRAVERSION"):
            extraversion = line.split("=")[1].strip()
    return "v{}.{}.{}{}".format(version, patchlevel, sublevel, extraversion)


def update_url(bot, url):
    LOG.info("Updating for %s" % url)
    ls_data = subprocess.check_output(["git", "ls-remote", url, "refs/heads/*"])
    ls_data = ls_data.decode("utf-8")
    ls_data = ls_data.strip()

    for tree in bot.config.git_tag.treelist:
        t_name, t_url = tree.split("#")
        if url == t_url:
            name = t_name
            break

    for head_data in ls_data.split("\n"):
        head_data = head_data.split("\t")
        commit = head_data[0]
        branch = head_data[1]
        branch = branch.replace("refs/heads/", "")
        treebranch = "{}#{}".format(name, branch)

        if treebranch in bot.config.git_tag.ignore_branches:
            continue

        makefile_url = get_makefile_url(url, commit)

        http = requests.get(makefile_url)
        if http.status_code == 302 or http.status_code == 404:
            continue
        toplines = http.content.decode("utf-8").split("\n")
        git_tag = get_git_tag(toplines[:6])
        git_describe = "{} ({})".format(git_tag, commit)
        if treebranch in bot.memory["git_tag"]:
            if bot.memory["git_tag"][treebranch] != git_describe:
                bot_say(bot, "{} has new version {}".format(treebranch, git_describe))
                bot.memory["git_tag"][treebranch] = git_describe
            else:
                LOG.info(
                    "{} has not changed tag from {}".format(treebranch, git_describe)
                )
        else:
            LOG.info(
                "no tag record for {}, setting to {}".format(treebranch, git_describe)
            )
            bot.memory["git_tag"][treebranch] = git_describe


def get_makefile_url(url, commit):
    if "github.com" in url:
        github_user, github_project = url.split("/")[3:5]
        makefile_url = "https://raw.githubusercontent.com/{}/{}/{}/Makefile".format(
            github_user, github_project, commit
        )
    else:
        makefile_url = "{}/plain/Makefile?h={}".format(url, commit)

    return makefile_url


@interval(120)
def xmlrpc_update(bot):
    if "git_tag" not in bot.memory:
        bot.memory["git_tag"] = {}
    if "manifest_fingerprints" not in bot.memory:
        bot.memory["manifest_fingerprints"] = {}

    # Fetch new manifest from git.kernel.org
    manifest_ret = None
    try:
        LOG.info("Fetching kernel.org manifest")
        manifest_ret = subprocess.call(
            [
                "/usr/bin/wget",
                "-qN",
                "-P",
                "/tmp",
                "https://git.kernel.org/manifest.js.gz",
            ]
        )
    except (FileNotFoundError, CalledProcessError) as e:
        LOG.info("Error calling on wget. Can't get manifest.js.gz.")

    # Get the fingerprint for
    for tree in bot.config.git_tag.treelist:
        name, url = tree.split("#")
        if "https://git.kernel.org/" in url:
            # Did we fetch the manifest?
            if manifest_ret != 0:
                LOG.info("Manifest ret != 0")
                continue
            key = url.replace("https://git.kernel.org", "")
            cmd = """zcat /tmp/manifest.js.gz | jq -r '{"%s"}[] | .fingerprint'""" % key
            fingerprint = subprocess.check_output(cmd, shell=True).decode().strip()
            LOG.info("Fingerprint for %s [%s]" % (name, fingerprint))
            if url in bot.memory["manifest_fingerprints"]:
                LOG.info(
                    "Fingerprints in memory for %s: %d"
                    % (name, len(bot.memory["manifest_fingerprints"]))
                )
                if bot.memory["manifest_fingerprints"][url] != fingerprint:
                    LOG.info(
                        "Fingerprint changed for %s: %s (was %s)"
                        % (url, fingerprint, bot.memory["manifest_fingerprints"][url])
                    )
                    update_url(bot, url)
                    bot.memory["manifest_fingerprints"][url] = fingerprint
            else:
                LOG.info("New fingerprint for %s: %s" % (url, fingerprint))
                bot.memory["manifest_fingerprints"][url] = fingerprint
                update_url(bot, url)
        else:
            LOG.info("Looking at non-git.kernel.org tree")
            update_url(bot, url)
