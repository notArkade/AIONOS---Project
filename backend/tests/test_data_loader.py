from collections import Counter

from app.services.data_loader import SourceDataLoader


def test_all_five_email_threads_exist_with_five_messages_each() -> None:
    emails = SourceDataLoader().load_emails().emails

    counts = Counter(email.thread_id for email in emails)

    assert counts == {
        "vendor-list": 5,
        "q3-campaign-deck": 5,
        "call-reschedule": 5,
        "expense-variance-report": 5,
        "mumbai-office-lease-renewal": 5,
    }


def test_calendar_data_loads() -> None:
    calendar = SourceDataLoader().load_calendar()

    assert len(calendar.calendar_events) == 34
    assert calendar.calendar_events[0].event == "Leadership Sync"


def test_meeting_data_loads() -> None:
    meetings = SourceDataLoader().load_meetings()

    assert len(meetings.meetings) == 1
    assert meetings.meetings[0].title == "Leadership Sync"
    assert len(meetings.meetings[0].transcript) == 10


def test_two_voice_notes_load() -> None:
    voice_notes = SourceDataLoader().load_voice_notes()

    assert len(voice_notes.voice_notes) == 2
    assert voice_notes.voice_notes[0].speaker == "Arjun Malhotra"


def test_people_data_loads() -> None:
    people = SourceDataLoader().load_people()

    assert len(people.people) == 6
    assert [person.name for person in people.people if person.is_application_user] == [
        "Arjun Malhotra"
    ]
