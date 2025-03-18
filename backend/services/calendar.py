from datetime import datetime


def create_ics_file(title: str, description: str, start_date: str, end_date: str) -> str:
    """Generate an iCalendar (.ics) formatted string."""
    start_dt = datetime.fromisoformat(str(start_date)).strftime("%Y%m%dT%H%M%SZ")
    end_dt = datetime.fromisoformat(str(end_date)).strftime("%Y%m%dT%H%M%SZ")

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:{title}
DESCRIPTION:{description}
DTSTART:{start_dt}
DTEND:{end_dt}
END:VEVENT
END:VCALENDAR"""
    return ics_content