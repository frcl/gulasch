# gulasch

View the Fahrplan for #gpn19 from your terminal. Type

	$ curl frcl.de/gulasch

and get

```
Next talks from 2019-05-30 16:00

        | ZKM_Medientheater  | ZKM_OpenHUB        | ZKM_Vortragssaal   | ZKM_CodeHUB        | Lounge
16:00 --┌────────────────────┐------------------------------------------------------------------------------------
        │                    │
        │  What to hack      │
        │                    │
        │  Christian L…  de  │
        │                    │
16:30 --├────────────────────┤------------------------------------------------------------------------------------
        │                    │
        │  Die Vorbereitun…  │
        │                    │
        │  skyangel      de  │
        │                    │
17:00 --├────────────────────┼────────────────────┐--------------------┌────────────────────┐---------------------
        │                    │                    │                    │                    │
        │  Schlangenprogra…  │  Open_Open Codes   │                    │  Dein eigener,     │
        │                    │                    │                    │  selbst gelöteter  │
        │  Thomas Kolb   de  │  Blanca Gimé…  de  │                    │  LED-Regenbogen.   │
        │                    │                    │                    │                    │
17:30 --└────────────────────┴────────────────────┘--------------------│                    │---------------------
                                                                       │                    │
                                                                       │                    │
        ┌────────────────────┬────────────────────┬────────────────────┤                    │
        │                    │                    │                    │                    │
        │  Hacking Building  │  Software testen?  │  Documentation     │                    │
18:00 --│  Automation        │  Ja bitte!         │  with any editor   │                    ├────────────────────┐
        │  Security - or     │                    │                    │                    │                    │
        │  how to have       │                    │                    │                    │  Skorpy            │
        │  keyless entry a…  │                    │                    │                    │                    │
        │                    │                    │                    │                    │                    │
        │                    │                    │                    │                    │                    │
18:30 --│                    │                    │                    │                    │                    │
        │  Kevin Heneka  de  │  Daniel Kule…  de  │  Christoph S…  en  │                    │                    │
        │                    │                    │                    │                    │                    │
        └────────────────────┴────────────────────┴────────────────────┤                    │                    │
                                                                       │                    │                    │
                                                                       │                    │                    │
19:00 -----------------------------------------------------------------│                    │                    │
                                                                       │                    │                    │
                                                                       │                    │                    │
                                                                       │                    │                    │
                                                                       │                    │                    │
                                                                       │                    │                    │
19:30 -----------------------------------------------------------------│                    │                    │
                                                                       │                    │                    │
                                                                       │                    │                    │
                                                                       │                    │                    │
                                                                       │  anathem       de  │  Lounge Cont…  en  │
                                                                       │                    │                    │
20:00 -----------------------------------------------------------------└────────────────────┴────────────────────┘
```
## Usage

By default `frcl.de/gulasch` returns a nicely formatted timetable of events starting in the next two ours.
You can control the dispalyed data with parameters.

If the timetable is to large for your needs it can get a more compact list with

	$ curl frcl.de/gulasch\?format=list

(Notice that the `?` needs to be escaped for most shells, alternativly use a quoted string as URL.)
If you want to reuse the data, `format=json` gets you a machine readable version.

You can extend the time period for dispalyed events with the `within` parameters.

	$ curl frcl.de/gulasch\?within=4h

It accepts hours with `h` or minutes with `min`.

The `from` parameter lets you see the events from the future.
For example all events on day 2 starting at noon:

	$ curl frcl.de/gulasch\?from=2019-05-31T12:00\&within=12h

## Server installation and usage

If you want to run the server on your own machine, clone the git repository and run

	pipenv run python gulaschkanone.py -f data.json -p 8080

You can then find the Fahrplan under `localhost:8080/gulasch`.
