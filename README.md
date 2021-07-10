# check_nsupdates

## Documentation

Nagios Plugin which checks if an update is available for a Citrix NetScaler.

The plugin connects to citrix.com and parses the [RSS feed](https://www.citrix.com/content/citrix/en_us/downloads/netscaler-adc.rss) to get a dict of all available NetScaler relases and the latest available build per release.

To get the installed version of the target NetScaler the plugin uses the NITRO API.

## Dependencies

- python-feedparser
- python-requests
- python-packaging

## Usage

```
# check with default credentials
./check_nsupdates.py -U http://10.0.0.100
WARNING: http://10.0.0.240: update available (installed: 13.0 71.44, available: 13.0 82.42)

# check with credentials given via cli
./check_nsupdates.py -U http://10.0.0.100 -u admin -p admin
WARNING: http://10.0.0.240: update available (installed: 13.0 71.44, available: 13.0 82.42)

# check with credentials given by ENV
export NETSCALER_USERNAME=admin
export NETSCALER_PASSWORD=admin
./check_nsupdates.py -U http://10.0.0.100
WARNING: http://10.0.0.240: update available (installed: 13.0 71.44, available: 13.0 82.42)
```

## Author

- [slauger](https://github.com/slauger)
