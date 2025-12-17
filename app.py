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
st.subheader("Add New Event")

with st.form("event_form", clear_on_submit=True):
    # From datetime (date + time on same row)
    st.markdown("**From**")
    from_col1, from_col2 = st.columns(2)
    with from_col1:
        from_date = st.date_input("Date", value=datetime.date.today(), key="from_date")
    with from_col2:
        from_time = st.time_input("Time", value=datetime.time(0, 0), key="from_time", step=60)

    # To datetime (date + time on same row)
    st.markdown("**To**")
    to_col1, to_col2 = st.columns(2)
    with to_col1:
        to_date = st.date_input("Date", value=datetime.date.today(), key="to_date")
    with to_col2:
        to_time = st.time_input("Time", value=datetime.time(23, 59), key="to_time", step=60)

    repeats = st.selectbox(
        "Repeats",
        options=["NONE", "DAILY", "WEEKLY", "MONTHLY", "ANNUALLY"],
        index=0
    )

    description = st.text_input("Description", placeholder="Enter event description")

    submitted = st.form_submit_button("Add Event", use_container_width=True)

    if submitted:
        if description.strip():
            from_datetime = datetime.datetime.combine(from_date, from_time)
            to_datetime = datetime.datetime.combine(to_date, to_time)

            if to_datetime >= from_datetime:
                st.session_state.entries.append({
                    "from_date": from_datetime,
                    "to_date": to_datetime,
                    "repeats": repeats,
                    "description": description.strip()
                })
                st.success("Event added!")
            else:
                st.error("End date/time must be after start date/time.")
        else:
            st.error("Please enter a description.")

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

    # Prepare display data
    display_data = []
    for i, entry in enumerate(st.session_state.entries[start_idx:end_idx], start=start_idx + 1):
        display_data.append({
            "#": i,
            "From": entry["from_date"].strftime("%Y-%m-%d %H:%M"),
            "To": entry["to_date"].strftime("%Y-%m-%d %H:%M"),
            "Repeats": entry["repeats"],
            "Description": entry["description"]
        })

    # Display table
    st.table(display_data)

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
