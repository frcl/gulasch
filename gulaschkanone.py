# pylint: disable=import-error
import asyncio
import json  # for decoding 'fahrplan.json'
import sys  # for meta information
import textwrap  # for wraping text in event cards
from datetime import datetime, timedelta

import aiohttp
from aiohttp import web
from dateutil import rrule
# from tabulate import tabulate
# from tinydb import TinyDB, Query


__version__ = 'v0.1.0'


# =========
# TEMPLATES
# =========


FAHRPLAN_JSON_URL = 'http://localhost:9000/fahrplan17.json'
# FAHRPLAN_JSON_URL = 'https://entropia.de/GPN17:Fahrplan:JSON?action=raw'

# LOCK = asyncio.Lock()
DATA = {'events': [],
        'locations': [],
        'speakers': []}
META_DATA = {'last_update': None,
             'version': __version__,
             'py_version': sys.version[:5],
             'aio_version': aiohttp.__version__}
META_TEMPL = """\033[1m\033[33mgulaschkanone {version}\033[0m
Running on Python {py_version} with aiohttp {aio_version}.
The last update was at {last_update}.
For usage info see \033[33mhttp://frcl.de/gulasch/help\033[0m
Found a bug? Open an issue at \033[33mhttps://github.com/frcl/gulaschkanone\033[0m
"""
HELP_TEXT = """TODO
"""
GULASCH_TEMPL = """\033[1m\033[33mNext talks from {now:%Y-%m-%d %H:%M}\033[0m
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
    if (len(parts), len(parts[0]), len(parts[1])) != (2, 2, 2):
        raise ValueError('not a duration: {}'.format(dur_str))
    hrs, mins = int(parts[0]), int(parts[1])
    if mins >= 60 or hrs < 0 or mins < 0:
        raise ValueError('not a duration: {}'.format(dur_str))
    return 60*hrs + mins


def get_next_events(now, within_mins=60):
    for event in DATA['events']:
        if timedelta(0) <= event['start']-now <= timedelta(minutes=within_mins):
            yield event


def timetable(events):
    by_location = {e['location']: e for e in events}
    start = min(e['start'] for e in events)
    end = max(e['start']+timedelta(minutes=e['duration']) for e in events)

    col_width = 20
    yield '|'.join([' '*8] + [f' {loc:<{col_width-2}} ' for loc in by_location]) + '|'
    # TODO: fix loc order using DATA['location']

    cards = [card(ev, col_width) for ev in by_location.values()]
    for dt in rrule.rrule(rrule.HOURLY, byminute=(0, 30),
                          dtstart=start, until=end):
        yield dt.strftime('%H:%M') + ' ---' + '-'*(col_width+1)*len(by_location)

        for td in map(lambda x: timedelta(minutes=x), range(5, 30, 5)):
            time = dt + td
            yield f'{time:%H:%M}'


def card(event, col_width):
    yield ' '*20

    dur = event['duration']
    if dur >= 30:
        max_title_lines = 1
        padding_lines = 1
    if dur >= 60:
        max_title_lines = 5
        padding_lines = 3

    text_width = col_width - 2
    lines = textwrap.wrap(event['title'], text_width)
    if len(lines) > max_title_lines:
        last_line = lines[max_title_lines-1]
        if len(last_line) > col_width - 4:
            lines[max_title_lines-1] = last_line[:col_width-5] + '…'

    for i in range(max_title_lines):
        try:
            yield f'  {lines[i]:<{col_width-4}}  '
        except IndexError:
            yield ' '*20

    for _ in range(padding_lines):
        yield ' '*20

    speaker_str = ', '.join(event['speakers'])
    if len(speaker_str) > col_width - 8:
        speaker_str = speaker_str[:col_width-9] + '…'
    yield f'  {speaker_str:<{col_width-8}}  {event["language"]}  '

    yield ' '*20


# TEST_EVENTS = [
    # dict(id=1, start=datetime(2017, 5, 28, 23, 0), duration=60,
         # location='room1', type='', language='en',
         # title='Foo ads afsfsd afas aefeoc gwrsrgaw aeaflkvsjn smsdasajdnk adadf akdjn',
         # subtitle='',
         # do_not_record=True, speakers=['John'], links=[]),
    # dict(id=2, start=datetime(2017, 5, 29, 0, 34), duration=30,
         # location='room2', type='', language='de', title='Bar', subtitle='',
         # do_not_record=True, speakers=['Kevin'], links=[]),
    # dict(id=3, start=datetime(2017, 5, 28, 23, 42), duration=60,
         # location='room3', type='', language='de', title='Spam', subtitle='',
         # do_not_record=True, speakers=['F. Bar', 'S. Eggs'], links=[]),
    # dict(id=4, start=datetime(2017, 5, 29, 1, 0), duration=60,
         # location='room4', type='', language='en', title='Eggs', subtitle='',
         # do_not_record=True, speakers=['Very very long name for a speaker'], links=[]),
# ]


# print('\n'.join(timetable(TEST_EVENTS)))
# for ev in TEST_EVENTS:
    # print('\n'.join(card(ev, 20)))
    # print('-'*20)
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
    # now = datetime.now()
    now = datetime.fromisoformat('2017-05-27T21:34:00+02:00')
    style = request.query.get('style', 'list')
    if style not in ('list',):
        resp = web.Response(text=f'ERROR: unknown style "{style}"\n',
                            content_type='text/plain')
    else:
        events = sorted(get_next_events(now, within_mins=120),
                        key=lambda x: x['start'])
        table_lines = ['* \033[33m{:%H:%M}\033[0m {} - {}\n'
                       .format(ev['start'], ev['title'], ev['subtitle'])
                       for ev in events]
        resp = web.Response(text=GULASCH_TEMPL.format(lines), content_type='text/plain')
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


# tmp
# async def handle_all_request(request):
    # import pprint
    # return web.Response(text=pprint.pprint(DATA))


# if __name__ == '__main__':
    # with open('data.json') as jfile:
        # DATA['events'] = normalize(json.load(jfile))
    # app = web.Application()
    # app.on_startup.append(start_background_tasks)
    # app.add_routes([web.get('/help', usage),
                    # web.get('/meta', handle_meta_request),
                    # # web.get('/all', handle_all_request),
                    # web.get('/', handle_gulasch_request)])
    # web.run_app(app)
