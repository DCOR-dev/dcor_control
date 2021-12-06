#!/bin/bash
#
# Run all background jobs on resources created in the past day.
#
# Put this script in /root/scripts, make it executable and add the
# following cron job:
#
# # purge datasets every sunday morning
# 30 1 * * * root /root/scripts/cron_run_jobs_dcor.sh > /dev/null
#
source /usr/lib/ckan/default/bin/activate
export CKAN_INI=/etc/ckan/default/ckan.ini
ckan run-jobs-dcor-depot --modified-days 1
ckan run-jobs-dcor-schemas --modified-days 1
ckan run-jobs-dc-view --modified-days 1
ckan run-jobs-dc-serve --modified-days 1
