# pylint: disable=import-error
import asyncio
import json
import sys
from datetime import datetime

import aiohttp
from aiohttp import web
from dateutil import rrule
# from tabulate import tabulate


__version__ = 'v0.1.0'


# =========
# TEMPLATES
# =========


FAHRPLAN_JSON_URL = 'http://localhost:9000/fahrplan17.json'
# FAHRPLAN_JSON_URL = 'https://entropia.de/GPN17:Fahrplan:JSON?action=raw'

# with open('data.json') as jfile:
    # DATA = json.load(jfile)
LOCK = asyncio.Lock()
META_DATA = {'last_update': None,
             'version': __version__,
             'py_version': sys.version[:5],
             'aio_version': aiohttp.__version__}
META_TEMPL = """\033[1m\033[33mgulaschkanone {version}\033[0m
Running on Python {py_version} with aiohttp {aio_version}.
The last update was at {last_update}.
"""
HELP_TEXT = """TODO
"""
CARD_TEMPL = """\033[1m\033[33mNext talks:\033[0m
{table}
"""
GULASCH_TEMPL = """\033[1m\033[33mNext talks:\033[0m
{table}
"""


# ====================
# Data transformations
# ====================


def normalize(data):
    by_day = data['schedule']['conference']['days']
    # locations = set()
    # speakers = set()
    events = []

    for day in by_day:
        for loc_name, ev_in_loc in day['rooms'].items():
            # locations.union(loc_name)
            for event in ev_in_loc:
                events.append(normalize_event(event))
                # speakers.union(event['persons'])

    # return locations, speakers, events
    return events


def normalize_event(event):
    return dict(
        id=int(event['id']),
        start=datetime.fromisoformat(event['date']),
        duration=parse_duration(event['duration']),
        location=event['room'],
        type=event['type'],
        language=event['language'],
        title=event['title'],
        subtitle=event['subtitle'],
        do_not_record=bool(event['do_not_record']),
        speakers=[person['public_name'] for person in event['persons']],
        links=[link['url'] for link in event['links']],
    )


def parse_duration(dur_str):
    """parse strings of the form 'HH:MM' and return number of minutes"""
    parts = dur_str.split(':')
    if not (parts, parts[0], parts[1]) == (2, 2, 2):
        raise ValueError('not a duration: {}'.format(dur_str))
    return 60*int(parts[0]) + int(parts[1])


TEST_EVENT = dict(
    id=1234,
    start=datetime.fromisoformat('2017-05-28T12:00:00+02:00'),
    duration=60,
    location='Studio',
    type='lecture',
    title='awsome talk',
    subtitle='amazing topic',
    track='GPN',
    language='en',
    do_not_record=False,
    speakers=['Jane Doe'],
    links=['https://example.com']
)


def get_next_events(now, until):
    return [TEST_EVENT]*3


# =======================
# Updata Mechanism (TODO)
# =======================


# async def update(now):
    # pass


# async def check_for_updates(app):
    # """background task for regularly calling update"""
    # await update(datetime.now())
    # for next_dt in rrule.rrule(rrule.DAILY, byhour=0):
        # await asyncio.sleep((next_dt-datetime.now()).seconds)
        # await update(next_dt)


# ================
# Request handlers
# ================


async def handle_gulasch_request(request):
    """entry point for /gulasch requests"""
    now = datetime.now()
    style = request.query.get('style', 'list')
    if style not in ('list',):
        resp = web.Response(text=f'ERROR: unknown style "{style}"',
                            content_type='text/plain')
    else:
        events = get_next_events(now, until=60)
        lines = [f'Next talks from {now:%Y-%m-%d %H:%M}'] + \
                ['* {:%H:%M}: {} - {}'.format(ev['start'], ev['title'], ev['subtitle'])
                 for ev in events]
        resp = web.Response(text='\n'.join(lines), content_type='text/plain')
    return resp


async def handle_meta_request(request):
    """entry point for /meta requests"""
    if 'format' in request.query and 'json' in request.query['format']:
        resp = web.json_response(META_DATA)
    else:
        resp = web.Response(text=META_TEMPL.format(**META_DATA),
                            content_type='text/plain')
    return resp


async def usage(request):
    return web.Response(text=HELP_TEXT, content_type='text/html')


async def start_background_tasks(app):
    # at the moment there are no updates
    # app['update_checker'] = app.loop.create_task(check_for_updates(app))
    pass


if __name__ == '__main__':
    app = web.Application()
    app.on_startup.append(start_background_tasks)
    app.add_routes([web.get('/help', usage),
                    web.get('/meta', handle_meta_request),
                    web.get('/', handle_gulasch_request)
                    ])
    web.run_app(app)
