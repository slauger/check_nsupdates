#!/usr/bin/env python3
#
# check_nsupdates.py
#
# https://github.com/slauger/check_nsupdates
#
# Checks if there is an update available for a Citrix NetScaler.
# The plugin parses the rss feed from citrix.com to get a list of
# all available releases.
#
# The plugin expects an IP address or an FQDN of an NetScaler Gateway
# vServer. The installed version of a NetScaler is exposed to the
# outside world in /epa/epa.html.
# 
# @author: Simon Lauger <simon@lauger.de>
# @version v1.3.0

import os
import re
import sys
import feedparser
import requests
import urllib3
import argparse
from packaging import version

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class check_nsversion:
  # RSS feed for Citrix NetScaler releases
  ctx_url = 'https://www.citrix.com/content/citrix/en_us/downloads/netscaler-adc.rss'

  # New - NetScaler Release (Feature Phase) 12.0 Build 57.19
  # New - NetScaler Release (Maintenance Phase) 11.1 Build 57.11
  # New - Citrix ADC Release (Feature Phase) 13.0 Build 41.20
  # New - Citrix ADC Release (Maintenance Phase) 12.1 Build 53.12
  ctx_pattern = 'New \- (NetScaler|Citrix ADC) Release( \(Feature Phase\)| \(Maintenance Phase\))? (1[0123]\.[0-9]) Build ([0-9]{2}\.[0-9]{1,2})'

  # NetScaler NS13.0: Build 71.44.nc, Date: Dec 26 2020, 11:31:14   (64-bit)
  ns_pattern = 'NetScaler NS(1[0123])\.([0-9]): Build ([0-9]{2})\.([0-9]{1,2}).*'

  # All major releases and latest available build per major version
  releases = {}

  # nagios return codes
  return_codes = {
    'OK': 0,
    'WARNING': 1,
    'CRITICAL': 2,
    'UNKOWN': 3,
  }

  # messages
  messages = []

  # plugin exitcode
  exitcode = 0

  # debug mode
  debug = False

  def __init__(self):
    self.feed  = feedparser.parse(self.ctx_url)
    self.ctx_regex = re.compile(self.ctx_pattern)
    self.ns_regex = re.compile(self.ns_pattern)
    self.parse()

  def set_baseurl(self, baseurl):
    self.baseurl = baseurl

  def set_username(self, username):
    self.username = username

  def set_password(self, password):
    self.password = password

  def set_debug(self, value):
    self.debug = bool(value)

  def parse(self):
    for item in self.feed['items']:
      matches = self.ctx_regex.match(item['title'])
      if matches:
        if not matches.group(3) in self.releases:
          self.releases[matches.group(3)] = matches.group(4)

  def get_relases(self, major = None):
    if major == None:
      return self.releases
    else:
      return self.releases[major]

  def add_message(self, exitcode, message):
    if exitcode > self.exitcode:
      self.exitcode = exitcode
    self.messages.append(message)

  def nagios_exit(self):
    for message in self.messages:
      print(message)
    sys.exit(self.exitcode)

  def check(self):
    url = self.baseurl + "/nitro/v1/config/nsversion"
    try:
      response = requests.get(url, verify=False, headers={
        'X-NITRO-USER': self.username,
        'X-NITRO-PASS': self.password,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      })
    except Exception as e:
      if self.debug:
        print(e)
      self.add_message(self.return_codes['CRITICAL'], "CRITICAL: http request to " + self.baseurl + " failed")
      return self.return_codes['CRITICAL']

    if response.status_code != 200:
      if self.debug:
        print(response.text)
      self.add_message(self.return_codes['CRITICAL'], "CRITICAL: http request to " + self.baseurl + " returned status code " + str(response.status_code))
      return self.return_codes['CRITICAL']

    version_str = response.json()['nsversion']['version']

    matches = self.ns_regex.match(version_str)

    major = str(matches.group(1) + '.' + matches.group(2))
    build = str(matches.group(3) + '.' + matches.group(4))

    if self.releases[major] == build or version.parse(self.releases[major]) < version.parse(build):
      self.add_message(self.return_codes['OK'], "OK: " + self.baseurl + ": up to date  (installed: " + major + " " + build + ", available: " + major + " " + self.releases[major] + ")")
      return self.return_codes['OK']
    else:
      self.add_message(self.return_codes['WARNING'], "WARNING: " + self.baseurl + ": update available (installed: " + major + " " + build + ", available: " + major + " " + self.releases[major] + ")")
      return self.return_codes['WARNING']

    self.add_message(self.return_codes['UNKOWN'], "UNKOWN: " + self.baseurl + ": could not find a nsversion string in response")
    return self.return_codes['UNKOWN']

if __name__ == '__main__':
  add_args = (
    {
      '--url': {
        'alias': '-U',
        'help': 'Base URL of the Citrix ADC. If not set the value from the ENV NETSCALER_URL is used.',
        'type': str,
        'default': None,
        'required': True,
      }
    },
    {
      '--username': {
        'alias': '-u',
        'help': 'Username for Citrix ADC. If not set the value from the ENV NETSCALER_USERNAME is used. Defaults to nsroot.',
        'type': str,
        'default': os.environ.get('NETSCALER_USERNAME', 'nsroot'),
        'required': False,
      }
    },
    {
      '--password': {
        'alias': '-p',
        'help': 'Password for Citrix ADC. If not set the value from the ENV NETSCALER_PASSWORD is used. Defaults to nsroot',
        'type': str,
        'default': os.environ.get('NETSCALER_PASSWORD', 'nsroot'),
        'required': False,
      }
    }
  )

  parser = argparse.ArgumentParser(description='Nagios Plugin which checks if an update is available for a Citrix ADC (formerly Citrix NetScaler)')

  for item in add_args:
    arg    = list(item.keys())[0]
    params = list(item.values())[0]
    parser.add_argument(
      params['alias'], arg,
      type=params['type'],
      help=params['help'],
      default=params['default'],
      required=params['required'],
    )

  parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose mode and print the requests python response')

  # parse args
  args = parser.parse_args()

  # start plugin and parse rss feed
  plugin = check_nsversion()

  # check for url
  if not args.url:
    plugin.add_message(3, 'netscaler url is not defined or empty')
    plugin.nagios_exit()

  # add args to class
  plugin.set_baseurl(args.url)
  plugin.set_username(args.username)
  plugin.set_password(args.password)

  # debug mode
  if (args.verbose):
    plugin.set_debug(True)

  # run check
  plugin.check()

  # exit and print results
  plugin.nagios_exit()
