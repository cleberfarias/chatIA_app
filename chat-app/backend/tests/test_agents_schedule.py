import pytest
import asyncio
from datetime import datetime, timedelta

from bots.agents import sdr_schedule_event

class DummyCalendarService:
    def __init__(self):
        self.authenticated = True
    def authenticate(self):
        return True
    def create_meeting_event(self, **kwargs):
        return {
            'id': 'abc123',
            'htmlLink': 'https://calendar.google.com/event?eid=abc123',
            'hangoutLink': 'https://meet.google.com/test',
            'summary': kwargs.get('summary')
        }

@pytest.mark.asyncio
async def test_sdr_schedule_event(monkeypatch):
    # Mock GoogleCalendarService
    from integrations import google_calendar
    monkeypatch.setattr(google_calendar, 'GoogleCalendarService', DummyCalendarService)

    # Mock DB insert
    from database import calendar_events_collection
    inserted = {}
    async def fake_insert(doc):
        inserted['doc'] = doc
        class Result: pass
        return Result()
    monkeypatch.setattr(calendar_events_collection, 'insert_one', fake_insert)

    start = datetime.utcnow() + timedelta(days=1, hours=2)
    end = start + timedelta(hours=1)
    event = await sdr_schedule_event(
        start_datetime=start,
        end_datetime=end,
        customer_email='test@example.com',
        customer_name='Test User',
        customer_phone='(11) 99999-9999',
        user_id='user123',
        user_name='User',
        contact_id='contact123'
    )

    assert event is not None
    assert event['id'] == 'abc123'
    assert inserted['doc']['google_event_id'] == 'abc123'
    assert inserted['doc']['customer_email'] == 'test@example.com'
