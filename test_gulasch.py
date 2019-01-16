from datetime import datetime, timedelta, timezone
import pytest
# tested module
import gulaschkanone as gk


def test_duration_parser():
    assert gk.parse_duration('01:00') == 60
    assert gk.parse_duration('00:42') == 42

    with pytest.raises(ValueError):
        gk.parse_duration('001:23')

    with pytest.raises(IndexError):
        gk.parse_duration('0123')

    with pytest.raises(ValueError):
        gk.parse_duration('02:63')


def test_event_normalization():
    norm_event = gk.normalize_event(dict(
        id=1234, date='2017-05-28T12:00:00+02:00', duration='01:00',
        room='myroom', type='test', language='en', title='Foo',
        subtitle='Bar', do_not_record=False,
        persons=[{'id': 12, 'public_name': 'John Doe'}],
        links=[{'url': 'http://example.com', 'title': 'Example'}]
    ))
    assert norm_event['start'] == datetime(
        2017, 5, 28, 12, 0, tzinfo=timezone(timedelta(seconds=7200)))
    assert norm_event['duration'] == 60
    assert norm_event['location'] == 'myroom'
    assert 'room' not in norm_event
    assert 'date' not in norm_event
    assert norm_event['links'] == ['http://example.com']
    assert norm_event['speakers'] == ['John Doe']


def test_next_events(monkeypatch):
    monkeypatch.setattr(gk, 'DATA', {'events': [
        dict(id=1, start=datetime(2017, 5, 28, 23, 0), duration='01:00',
             location='', type='', language='', title='', subtitle='',
             do_not_record=True, persons=[], links=[]),
        dict(id=2, start=datetime(2017, 5, 29, 0, 34), duration='01:00',
             location='', type='', language='', title='', subtitle='',
             do_not_record=True, persons=[], links=[]),
        dict(id=3, start=datetime(2017, 5, 28, 23, 42), duration='01:00',
             location='', type='', language='', title='', subtitle='',
             do_not_record=True, persons=[], links=[]),
        dict(id=4, start=datetime(2017, 5, 29, 1, 0), duration='01:00',
             location='', type='', language='', title='', subtitle='',
             do_not_record=True, persons=[], links=[]),
    ]})
    assert [ev['id'] for ev in gk.get_next_events(
        datetime(2017, 5, 28, 22, 50), within_mins=60)] == [1, 3]
