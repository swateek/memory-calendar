"""
Streamlit Calendar Entry App
A lightweight app for creating calendar events and exporting them to ICS format.
"""

import streamlit as st
import datetime
import uuid

# Page configuration
st.set_page_config(
    page_title="Calendar Entry",
    page_icon="📅",
    layout="centered"
)

# Initialize session state for entries
if "entries" not in st.session_state:
    st.session_state.entries = []

if "page" not in st.session_state:
    st.session_state.page = 0


def create_ics_event(start_dt, end_dt, description, repeats=None):
    """Creates a single ICS event string."""
    dt_format_full = "%Y%m%dT%H%M%S"
    now = datetime.datetime.now().strftime(dt_format_full)
    uid = str(uuid.uuid4())

    dt_start_str = f"DTSTART:{start_dt.strftime(dt_format_full)}"
    dt_end_str = f"DTEND:{end_dt.strftime(dt_format_full)}"

    event = [
        "BEGIN:VEVENT",
        f"DTSTAMP:{now}",
        f"UID:{uid}",
        dt_start_str,
        dt_end_str,
        f"SUMMARY:{description}",
        f"DESCRIPTION:{description}"
    ]

    if repeats and repeats != "NONE":
        freq = repeats.upper().strip()
        if freq == "ANNUALLY":
            freq = "YEARLY"
        if freq in ["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]:
            event.append(f"RRULE:FREQ={freq}")

    event.append("END:VEVENT")
    return "\n".join(event)


def generate_ics_content(entries):
    """Generates complete ICS file content from entries."""
    events = []
    for entry in entries:
        event = create_ics_event(
            entry["from_date"],
            entry["to_date"],
            entry["description"],
            entry["repeats"]
        )
        events.append(event)

    ics_content = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Calendar Entry App//Streamlit//EN",
        "CALSCALE:GREGORIAN"
    ]
    ics_content.extend(events)
    ics_content.append("END:VCALENDAR")

    return "\n".join(ics_content)


# App title
st.title("📅 Calendar Entry")
st.markdown("Create calendar events and export them to ICS format.")

# Form section
# Form section
st.subheader("Add New Event")

def sync_dates():
    if "from_date" in st.session_state and "to_date" in st.session_state:
        if st.session_state.to_date < st.session_state.from_date:
            st.session_state.to_date = st.session_state.from_date

# From datetime (date + time on same row)
st.markdown("**From**")
from_col1, from_col2 = st.columns(2)
with from_col1:
    from_date = st.date_input("Date", value=datetime.date.today(), key="from_date", on_change=sync_dates)
with from_col2:
    from_time = st.time_input("Time", value=datetime.time(0, 0), key="from_time", step=60)

# To datetime (date + time on same row)
st.markdown("**To**")
to_col1, to_col2 = st.columns(2)
with to_col1:
    # Ensure default value is valid if from_date is in future
    # Using min_value ensures the UI respects the constraint
    to_date = st.date_input("Date", value=max(datetime.date.today(), from_date), min_value=from_date, key="to_date")
with to_col2:
    to_time = st.time_input("Time", value=datetime.time(23, 59), key="to_time", step=60)

repeats = st.selectbox(
    "Repeats",
    options=["NONE", "DAILY", "WEEKLY", "MONTHLY", "ANNUALLY"],
    index=0,
    key="repeats"
)

description = st.text_input("Description", placeholder="Enter event description", key="description")

if "add_error" not in st.session_state:
    st.session_state.add_error = None

def add_event_callback():
    # Get values from session state
    # Note: widgets must have keys corresponding to these names
    desc = st.session_state.description
    
    if desc.strip():
        f_date = st.session_state.from_date
        f_time = st.session_state.from_time
        t_date = st.session_state.to_date
        t_time = st.session_state.to_time
        rep = st.session_state.repeats
        
        from_datetime = datetime.datetime.combine(f_date, f_time)
        to_datetime = datetime.datetime.combine(t_date, t_time)

        if to_datetime >= from_datetime:
            st.session_state.entries.append({
                "from_date": from_datetime,
                "to_date": to_datetime,
                "repeats": rep,
                "description": desc.strip()
            })
            # Clear description and error
            st.session_state.description = ""
            st.session_state.add_error = None
        else:
            st.session_state.add_error = "End date/time must be after start date/time."
    else:
        st.session_state.add_error = "Please enter a description."

st.button("Add Event", use_container_width=True, on_click=add_event_callback)

if st.session_state.add_error:
    st.error(st.session_state.add_error)

# Table section
st.divider()
st.subheader("Events")

if st.session_state.entries:
    # Pagination settings
    rows_per_page = st.selectbox("Rows per page", [5, 10, 20], index=0, key="rows_per_page")
    total_entries = len(st.session_state.entries)
    total_pages = (total_entries - 1) // rows_per_page + 1

    # Ensure page is in valid range
    if st.session_state.page >= total_pages:
        st.session_state.page = max(0, total_pages - 1)

    # Calculate slice indices
    start_idx = st.session_state.page * rows_per_page
    end_idx = min(start_idx + rows_per_page, total_entries)

    # Header
    h_col1, h_col2, h_col3, h_col4, h_col5 = st.columns([2, 2, 1, 3, 1])
    h_col1.markdown("**From**")
    h_col2.markdown("**To**")
    h_col3.markdown("**Repeats**")
    h_col4.markdown("**Description**")
    h_col5.markdown("**Action**")

    # Display rows
    for i, entry in enumerate(st.session_state.entries[start_idx:end_idx]):
        actual_index = start_idx + i
        c1, c2, c3, c4, c5 = st.columns([2, 2, 1, 3, 1])
        
        c1.write(entry["from_date"].strftime("%Y-%m-%d %H:%M"))
        c2.write(entry["to_date"].strftime("%Y-%m-%d %H:%M"))
        c3.write(entry["repeats"])
        c4.write(entry["description"])
        
        if c5.button("🗑️", key=f"delete_{actual_index}", help="Delete this event"):
            st.session_state.entries.pop(actual_index)
            # Adjust page if needed (if we deleted the last item on a page)
            if not st.session_state.entries:
                st.session_state.page = 0
            elif st.session_state.page > (len(st.session_state.entries) - 1) // rows_per_page:
                st.session_state.page = max(0, st.session_state.page - 1)
            st.rerun()

    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("← Previous", disabled=st.session_state.page == 0):
            st.session_state.page -= 1
            st.rerun()

    with col2:
        st.markdown(
            f"<p style='text-align: center;'>Page {st.session_state.page + 1} of {total_pages}</p>",
            unsafe_allow_html=True
        )

    with col3:
        if st.button("Next →", disabled=st.session_state.page >= total_pages - 1):
            st.session_state.page += 1
            st.rerun()

    # Export button
    st.divider()
    ics_content = generate_ics_content(st.session_state.entries)

    st.download_button(
        label="📥 Export to ICS",
        data=ics_content,
        file_name="events.ics",
        mime="text/calendar",
        use_container_width=True
    )

    # Clear all button
    if st.button("🗑️ Clear All Events", use_container_width=True):
        st.session_state.entries = []
        st.session_state.page = 0
        st.rerun()

else:
    st.info("No events yet. Add your first event above!")
