# gulasch

View the Fahrplan for #gpn19 from your terminal. Type

	$ curl localhost:8080/gulasch

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

## Server installation and usage

If you want to run the server on your own machine, clone the git repository and run

	pipenv run python gulaschkanone.py -f data.json -p 8080

You can then find the Fahrplan under `localhost:8080/gulasch`.
