# check_nsupdates

Nagios Plugin which checks if an update is available for a Citrix NetScaler.

The plugin connects to citrix.com and parses the [RSS feed](https://www.citrix.com/content/citrix/en_us/downloads/netscaler-adc.rss) to get a dict of all available NetScaler relases and the latest available build per release.

To get the installed version of the NetScaler the plugin makes use of the fact that the versioning for the NetScaler and the EPA clienttools is the same schema. The version of the hosted EPA client is exposed to the outside world in `/vpn/pluginlist.xml` on each NetScaler Gateway vServer.

Example:
```
-bash$ curl -q https://gateway.example.com/vpn/pluginlist.xml 2> /dev/null | egrep '.*version="(1[012])\.([0-9])\.([0-9]{2})\.([0-9]{2})".*' 
			version="12.1.48.13" 			path="/epa/scripts/win/nsepa_setup.exe"
			version="12.1.48.13" 			path="/epa/scripts/win/nsepa_setup64.exe"
			version="12.1.48.13" 			path="/vpns/scripts/vista/AGEE_setup.exe"
```

## Dependencies

- python-feedparser
- python-requests

## Usage

```
-bash$ ./check_nsupdates.py gateway1.example.com gateway2.example.com
WARNING: gateway1.example.com: update available (installed: 11.1 56.19, available: 11.1 57.11)
WARNING: gateway2.example.com: update available (installed: 12.0 56.20, available: 12.0 57.19)
```

## Author

- [slauger](https://github.com/slauger)
