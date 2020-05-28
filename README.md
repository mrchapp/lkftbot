Sample `default.cfg` to run Sopel with:
```
[core]
nick = lkftbot
host = chat.freenode.org
use_ssl = true
port = 6697
auth_method = nickserv
auth_username = lkftbot
auth_password = password
owner = owners_nick
channels = #linaro-lkft
logging_level = INFO

[git_tag]
treelist = stable-rc#https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux-stable-rc.git,stable#https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git
allowed_channels = #linaro-lkft
ignore_branches = stable-rc#queue/4.4,stable-rc#queue/4.9,stable-rc#queue/4.14,stable-rc#queue/4.19,stable-rc#queue/5.4,stable-rc#queue/5.5,stable-rc#queue/5.6

[jira]
base_url = https://projects.linaro.org
username = user.name@linaro.org
password = password
allowed_channels = #linaro-lkft

[gerrit]
base_url = https://review.linaro.org
allowed_channels = #linaro-lkft

[clock]
tz = UTC
time_format = %Y-%m-%d - %T%Z
```
