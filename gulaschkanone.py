# pylint: disable=import-error
import asyncio
import json  # for decoding 'fahrplan.json'
import sys  # for meta information
import textwrap  # for wraping text in event cards
from datetime import datetime, timedelta
from typing import Dict, Generator, List

import aiohttp
import pytz
from aiohttp import web
from dateutil import rrule


__version__ = 'v0.2.1'


# =========
# TEMPLATES
# =========


# FAHRPLAN_JSON_URL = 'https://entropia.de/GPN17:Fahrplan:JSON?action=raw'
GPN_START = datetime.fromisoformat('2019-05-30T16:00:00+02:00')
CEST = pytz.timezone('Europe/Berlin')

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
GULASCH_TEMPL = """\033[1m\033[33mNext talks from {now:%Y-%m-%d %H:%M}\033[0m\n
{table}
"""


# ====================
# Data transformations
# ====================


class Event:

    def __init__(self, data):
        self.data = data
        self.start = data['start']
        self.end = self.start + timedelta(minutes=data['duration'])
        # make data json serializable
        self.data['start'] = self.start.isoformat()

    def __getitem__(self, key):
        return self.data[key]

    def is_running_at(self, dt):
        return self.start < dt < self.end


def normalize(data):
    by_day = data['schedule']['conference']['days']
    locations = by_day[0]['rooms'].keys()
    # speakers = set()
    events = []

    for day in by_day:
        for loc_events in day['rooms'].values():
            for event in loc_events:
                events.append(Event(normalize_event(event)))
                # speakers.union(event['persons'])

    # return locations, speakers, events
    return locations, events


def normalize_event(event):
    # fix overlapping opening talks
    if int(event['id']) == 11:
        event['duration'] = '00:30'

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
        if timedelta(0) <= event.start-now <= timedelta(minutes=within_mins):
            yield event


def timetable(events: List[Dict[str, object]], col_width: int = 20) -> str:
    """Create a timetable string for events"""
    if not events:
        return 'Currently no upcoming events'

    global_start = min(e.start for e in events)
    global_end = max(e.end for e in events)

    # this puts uniq locations in canonical order
    event_locations = {e['location'] for e in events}
    locations = [loc for loc in DATA['locations'] if loc in event_locations]

    cards_by_id = {e['id']: card(e, col_width) for e in events}
    events_by_location = {loc: [e for e in events if e['location'] == loc]
                          for loc in locations}

    tick_times = rrule.rrule(rrule.HOURLY, byminute=(0, 30),
                             dtstart=global_start, until=global_end)

    lines = ['        |' + '|'.join(f' {loc:<{col_width-2}} ' for loc in locations)]

    UD = '│'
    LR = '─'
    seperators = {
        (False, True, True, False): '┬',
        (True, False, False, True): '┴',
        (False, False, True, True): '┤',
        (True, True, False, False): '├',
        (False, True, False, True): '┼',
        (True, False, True, False): '┼',
    }

    def get_seperator(*args):
        """(upright, downright, downleft, upleft): Tuple[bool] -> seperator: str"""
        if sum(args) >= 3:
            return '┼'
        elif sum(args) == 1:
            return ('└', '┌', '┐', '┘')[args.index(True)]
        else:
            return seperators[tuple(args)]

    for dt in rrule.rrule(rrule.HOURLY, byminute=range(0, 60, 5),
                          dtstart=global_start, until=global_end):
        line_parts = [f'{dt:%H:%M} --' if dt in tick_times else ' '*8]
        fill_char = '-' if dt in tick_times else ' '

        starting_events = {loc: next((e for e in events_by_location[loc] if e.start == dt), None)
                           for loc in locations}
        running_events = {loc: next((e for e in events_by_location[loc] if e.is_running_at(dt)), None)
                          for loc in locations}
        ending_events = {loc: next((e for e in events_by_location[loc] if e.end == dt), None)
                         for loc in locations}

        loc = locations[0]
        start, run, end = starting_events[loc], running_events[loc], ending_events[loc]

        if start or end:
            line_parts.append(get_seperator(bool(end), bool(start), False, False) +LR*col_width)
        elif run:
            line_parts.append(UD+next(cards_by_id[run['id']]))
        else:
            line_parts.append(fill_char*(col_width+1))

        for loc1, loc2 in zip(locations[:-1], locations[1:]):
            start1, run1, end1 = starting_events[loc1], running_events[loc1], ending_events[loc1]
            start2, run2, end2 = starting_events[loc2], running_events[loc2], ending_events[loc2]

            start_end = [end2, start2, start1, end1]

            if run1 and (start2 or end2):
                line_parts.append('├')
            elif run2 and (start1 or end1):
                line_parts.append('┤')
            elif any(start_end):
                line_parts.append(get_seperator(*map(bool, start_end)))
            elif run1 or run2:
                line_parts.append(UD)
            else:
                line_parts.append(fill_char)

            if run2:
                line_parts.append(next(cards_by_id[run2['id']]))
            elif start2 or end2:
                line_parts.append(LR*col_width)
            else:
                line_parts.append(fill_char*col_width)

        loc = locations[-1]
        start, run, end = starting_events[loc], running_events[loc], ending_events[loc]

        if start or end:
            line_parts.append(get_seperator(False, False, bool(start), bool(end)))
        elif run:
            line_parts.append(UD)
        else:
            line_parts.append(fill_char)

        lines.append(''.join(line_parts))

    return '\n'.join(lines)


def card(event: Dict[str, object], col_width: int) -> Generator[str, None, None]:
    """Generate the lines of an event card

    Arguments:
        event (Dict[str, object]): The event to display, used values are
            'title', 'duration', 'speakers' and 'language'
        col_width (int): The length each line should have
    """
    empty_line = ' '*col_width
    text_width = col_width - 4
    titlelines = textwrap.wrap(event['title'], text_width)
    height = event['duration']//5 - 1

    # shorten title if space is scarce
    if height <= 11:
        if height <= 5:
            max_title_lines = 1
        else:
            max_title_lines = 5
        if len(titlelines) > max_title_lines:
            titlelines = titlelines[:max_title_lines]
            lastln = titlelines[-1]
            if len(lastln) == text_width:
                titlelines[-1] = lastln[:text_width-1] + '…'
            else:
                titlelines[-1] = lastln + '…'

    # fit speaker(s) and language in one line
    speaker_str = ', '.join(event['speakers'])
    if len(speaker_str) > text_width - 4:
        speaker_str = speaker_str[:text_width-5] + '…'

    yield empty_line
    for line in titlelines:
        yield f'  {line:<{text_width}}  '
    for _ in range(height-len(titlelines)-3):
        yield empty_line
    yield f'  {speaker_str:<{text_width-4}}  {event["language"]:<2}  '
    yield empty_line


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
    now = datetime.now(tz=CEST)
    if now < GPN_START:
        now = GPN_START
    display_format = request.query.get('format', 'timetable')
    events = sorted(get_next_events(now, within_mins=120),
                    key=lambda x: x.start)

    if display_format == 'timetable':
        table = timetable(events)
        resp = web.Response(text=GULASCH_TEMPL.format(now=now, table=table),
                            content_type='text/plain')
    elif display_format == 'list':
        table = ''.join('* \033[33m{:%H:%M}\033[0m {}{}, {}; {}\n'
                        .format(ev.start, ev['title'],
                                ' - '+ev['subtitle'] if ev['subtitle'] else '',
                                ', '.join(ev['speakers']),
                                ev['language'])
                        for ev in events)
        resp = web.Response(text=GULASCH_TEMPL.format(now=now, table=table),
                            content_type='text/plain')
    elif display_format == 'json':
        resp = web.json_response([e.data for e in events])
    else:
        resp = web.Response(text=f'ERROR: unknown format "{display_format}"\n',
                            content_type='text/plain')

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
    import argparse
    argp = argparse.ArgumentParser()
    argp.add_argument('-f', '--data-file', default='data.json')
    argp.add_argument('-p', '--port', default=80)
    args = argp.parse_args()
    with open(args.data_file) as jfile:
        DATA['locations'], DATA['events'] = normalize(json.load(jfile))
    app = web.Application()
    app.on_startup.append(start_background_tasks)
    app.add_routes([web.get('/gulasch/help', usage),
                    web.get('/gulasch/meta', handle_meta_request),
                    web.get('/gulasch/', handle_gulasch_request),
                    web.get('/gulasch', handle_gulasch_request)])
    web.run_app(app, port=args.port)
