# TWCManager
TWCManager lets you control the amount of power delivered by a Generation 2 Tesla Wall Connector (TWC) to the car it's charging.  This can save around 6kWh per month when used to track a local green energy source like solar panels on your roof.  It can also avoid drawing grid energy for those without net metering or limit charging to times of day when prices are cheapest.

Due to hardware limitations, TWCManager will not work with Tesla's older High Power Wall Connectors (HPWCs) that were discontinued around April 2016.  TWCManager will also not work with Generation 3 TWCs released around Jan 15th 2020.  Sadly, gen 2 TWCs are no longer sold by Tesla and may become hard to acquire over time.  We don't expect to add support for gen 3 TWCs unless their wireless protocol is reverse engineered by a third party.

See **TWCManager Installation.pdf** for how to install and use.

## Modern Python entrypoint

This repository now runs through the modular Python 3.14 package in `twcmanager/`.

```sh
python3.14 -m twcmanager --help
python3.14 -m twcmanager --serial
```

`TWCManager.py` is kept only as a compatibility wrapper for `python3.14 TWCManager.py`.
