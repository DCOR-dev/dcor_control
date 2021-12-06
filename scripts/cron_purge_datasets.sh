#!/bin/bash
#
# Clear all datasets except for one from figshare on development machines.
#
# Put this script in /root/scripts, make it executable and add the
# following cron job:
#
# # purge datasets every sunday morning
# 5 0 * * 7 root /root/scripts/cron_purge_datasets.sh > /dev/null
#
source /usr/lib/ckan/default/bin/activate
export CKAN_INI=/etc/ckan/default/ckan.ini
# purge all datasets and zombie users
dcor reset --datasets --zombie-users --yes
# bring back first figshare dataset
ckan import-figshare --limit 1
# remove remaining orphans
dcor inspect --assume-yes
