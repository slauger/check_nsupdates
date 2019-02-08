#!/usr/bin/env python
#
# check_nsupdates.py
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
# @date:   2018-06-10
# @version v1.1.0

import re
import sys
import feedparser
import requests
import urllib3
from packaging import version

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class check_nsversion:
  # RSS feed for Citrix NetScaler releases
  ctx_url = 'https://www.citrix.com/content/citrix/en_us/downloads/netscaler-adc.rss'

  # New - NetScaler Release (Feature Phase) 12.0 Build 57.19
  # New - NetScaler Release (Maintenance Phase) 11.1 Build 57.11
  ctx_pattern = 'New \- NetScaler Release( \(Feature Phase\)| \(Maintenance Phase\))? (1[012]\.[0-9]) Build ([0-9]{2}\.[0-9]{1,2})'

  # var nsversion="12,0,57,19";
  ns_pattern = '.*version="(1[012])\.([0-9])\.([0-9]{2})\.([0-9]{1,2})".*'

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

  def __init__(self):
    self.feed  = feedparser.parse(self.ctx_url)
    self.ctx_regex = re.compile(self.ctx_pattern)
    self.ns_regex = re.compile(self.ns_pattern)
    self.parse()

  def parse(self):
    for item in self.feed['items']:
      matches = self.ctx_regex.match(item['title'])
      if matches:
        if not matches.group(2) in self.releases:
          self.releases[matches.group(2)] = matches.group(3)

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
  
  def check(self, fqdn):
    url = "https://" + fqdn + "/vpn/pluginlist.xml"
    try:
      response = requests.get(url, verify=False)
    except:
      self.add_message(self.return_codes['CRITICAL'], "CRITICAL: " + fqdn + " is unreachable")
      return self.return_codes['CRITICAL']
    for line in response.iter_lines():
      matches = self.ns_regex.match(line)
      if matches:
        major = str(matches.group(1) + '.' + matches.group(2))
        build = str(matches.group(3) + '.' + matches.group(4))
        if self.releases[major] == build or version.parse(self.releases[major]) < version.parse(build):
          self.add_message(self.return_codes['OK'], "OK: " + fqdn + ": up to date  (installed: " + major + " " + build + ", available: " + major + " " + self.releases[major] + ")")
          return self.return_codes['OK']
        else:
          self.add_message(self.return_codes['WARNING'], "WARNING: " + fqdn + ": update available (installed: " + major + " " + build + ", available: " + major + " " + self.releases[major] + ")")
          return self.return_codes['WARNING']
    self.add_message(self.return_codes['UNKOWN'], "UNKOWN: " + fqdn + ": could not find a nsversion string in response")
    return self.return_codes['UNKOWN']

# check if a arugment is given to the script
if len(sys.argv) < 2:
  print("usage: " + sys.argv[0] + " <hostname> [<hostname>] [...]")
  sys.exit(check_nsversion.return_codes['UNKOWN'])

# start plugin and parse rss feed
plugin = check_nsversion()

# check all hosts
for fqdn in sys.argv:
  if fqdn == sys.argv[0]:
    continue
  plugin.check(fqdn)

# exit and print results
plugin.nagios_exit()
