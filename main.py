import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
from utils import filter_programs, geocode_address, load_and_process_data, get_unique_values

# Force light theme configuration
st.set_page_config(
    page_title="After-School Finder",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Helper functions for display
def display_program_card(program):
    """Display a program as a card in list view"""
    with st.container():
        html = f"""
        <div class='program-card-container'>
            <h3 class='program-card-title'>{program.get('Program Name', 'N/A')}</h3>
            <p class='program-card-provider'>{program.get('Provider Name', 'N/A')}</p>
            <div class='program-card-info-bar'>
                <p class='program-card-text'><span style='margin-right: 8px;'>⏰</span>{program.get('Day of the week', 'N/A')} • {program.get('Start time', 'N/A')} - {program.get('End time', 'N/A')}</p>"""
        
        # Add cost and distance to key info bar
        if 'Distance' in program and not pd.isna(program['Distance']):
            html += f"<p class='program-card-text'><span style='margin-right: 8px;'>📍</span>{program['Distance']:.2f} miles away</p>"
        
        cost_info = []
        enrollment_type = program.get('Enrollment Type', '').strip() if isinstance(program.get('Enrollment Type'), str) else ''
        
        if 'Cost' in program and not pd.isna(program['Cost']):
            base_cost = f"${program['Cost']:.2f}"
            if enrollment_type:
                if 'semester' in enrollment_type.lower():
                    base_cost += "/semester"
                elif 'monthly' in enrollment_type.lower():
                    base_cost += "/month"
                elif 'drop' in enrollment_type.lower():
                    base_cost += " (drop-in)"
                else:
                    base_cost += f" ({enrollment_type.lower()})"
            cost_info.append(base_cost)
        
        if 'Cost Per Class' in program and not pd.isna(program['Cost Per Class']):
            cost_info.append(f"${program['Cost Per Class']:.2f}/class")
        
        if cost_info:
            html += f"<p class='program-card-text'><span style='margin-right: 8px;'>💰</span>{' • '.join(cost_info)}</p>"
        html += "</div>"
        
        # Secondary details
        min_age_val = program.get('Min Age', 0)
        max_age_val = program.get('Max Age', 0)
        min_age_safe = int(float(min_age_val)) if min_age_val is not None and not pd.isna(min_age_val) else 0
        max_age_safe = int(float(max_age_val)) if max_age_val is not None and not pd.isna(max_age_val) else 0
        html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>👶</span><strong>Ages:</strong> {min_age_safe} - {max_age_safe}</p>"
        html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>🎯</span><strong>Category:</strong> {program.get('Interest Category', 'N/A')}</p>"
        html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>📍</span><strong>Address:</strong> {program.get('Address', 'N/A')}</p>"
        
        # Contact & additional info
        if 'Website' in program and not pd.isna(program['Website']):
            html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>🌐</span><a href='{program['Website']}' target='_blank' class='program-card-link'>Website</a></p>"
        if 'Contact Phone' in program and not pd.isna(program['Contact Phone']):
            html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>📞</span><strong>Phone:</strong> {program['Contact Phone']}</p>"
        if 'School Pickup From' in program and isinstance(program['School Pickup From'], str) and program['School Pickup From'].strip():
            html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>🚌</span><strong>School pickup:</strong> {program['School Pickup From']}</p>"
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

def parse_time(time_str):
    """Parse time string to minutes from midnight for sorting"""
    if not time_str or pd.isna(time_str):
        return 0
    try:
        time_str = str(time_str).strip()
        if 'AM' in time_str or 'PM' in time_str:
            time_part = time_str.replace('AM', '').replace('PM', '').strip()
            hour, minute = map(int, time_part.split(':'))
            if 'PM' in time_str and hour != 12:
                hour += 12
            elif 'AM' in time_str and hour == 12:
                hour = 0
            return hour * 60 + minute
        else:
            # Assume 24-hour format
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
    except:
        return 0

def minutes_to_time_str(minutes):
    """Convert minutes from midnight to time string"""
    hour = minutes // 60
    minute = minutes % 60
    if hour == 0:
        return f"12:{minute:02d} AM"
    elif hour < 12:
        return f"{hour}:{minute:02d} AM"
    elif hour == 12:
        return f"12:{minute:02d} PM"
    else:
        return f"{hour-12}:{minute:02d} PM"

def calculate_duration_minutes(start_time, end_time):
    """Calculate duration between start and end times in minutes"""
    start_minutes = parse_time(start_time)
    end_minutes = parse_time(end_time)
    if start_minutes > 0 and end_minutes > 0 and end_minutes > start_minutes:
        return end_minutes - start_minutes
    return 0

def format_duration(minutes):
    """Format duration in minutes to readable string"""
    if minutes <= 0:
        return ""
    elif minutes < 60:
        return f"({minutes} min)"
    else:
        hours = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"({hours}h)"
        else:
            return f"({hours}h {mins}m)"

def get_category_icon(category):
    """Get icon for program category"""
    if not category or pd.isna(category):
        return "📚"
    
    category_lower = str(category).lower()
    
    if any(word in category_lower for word in ['art', 'craft', 'draw', 'paint', 'creative']):
        return "🎨"
    elif any(word in category_lower for word in ['sport', 'soccer', 'basketball', 'tennis', 'swim', 'athletic', 'physical']):
        return "⚽"
    elif any(word in category_lower for word in ['music', 'piano', 'guitar', 'sing', 'band', 'choir']):
        return "🎵"
    elif any(word in category_lower for word in ['stem', 'science', 'math', 'coding', 'robot', 'engineering', 'tech']):
        return "🔬"
    elif any(word in category_lower for word in ['dance', 'ballet', 'hip hop']):
        return "💃"
    elif any(word in category_lower for word in ['academic', 'tutor', 'homework', 'study']):
        return "📚"
    elif any(word in category_lower for word in ['language', 'spanish', 'french', 'chinese']):
        return "🗣️"
    else:
        return "📚"

def get_distance_badge_info(distance):
    """Get distance badge class and text"""
    if pd.isna(distance) or distance <= 0:
        return "", ""
    
    if distance < 1:
        return "distance-close", f"{distance:.1f}mi"
    elif distance <= 2:
        return "distance-medium", f"{distance:.1f}mi"
    else:
        return "distance-far", f"{distance:.1f}mi"

def add_program_to_schedule(program, schedule_name):
    """Add a program to a named schedule"""
    if schedule_name not in st.session_state.saved_schedules:
        st.session_state.saved_schedules[schedule_name] = []
    
    # Create program data dictionary
    program_data = {
        'Program Name': program.get('Program Name', 'N/A'),
        'Provider Name': program.get('Provider Name', 'N/A'),
        'Day of the week': program.get('Day of the week', ''),
        'Start time': program.get('Start time', ''),
        'End time': program.get('End time', ''),
        'Interest Category': program.get('Interest Category', ''),
        'Distance': program.get('Distance', 0),
        'Address': program.get('Address', ''),
        'Cost': program.get('Cost', 0),
        'Website': program.get('Website', ''),
        'Contact Phone': program.get('Contact Phone', ''),
    }
    
    # Check if program already exists in schedule (match by name, provider, day, and time)
    existing_programs = st.session_state.saved_schedules[schedule_name]
    for existing in existing_programs:
        if (existing['Program Name'] == program_data['Program Name'] and 
            existing['Provider Name'] == program_data['Provider Name'] and
            existing['Day of the week'] == program_data['Day of the week'] and
            existing['Start time'] == program_data['Start time']):
            return False  # Already exists
    
    st.session_state.saved_schedules[schedule_name].append(program_data)
    return True

def detect_schedule_conflicts(schedule_name):
    """Detect time conflicts within a schedule"""
    if schedule_name not in st.session_state.saved_schedules:
        return []
    
    programs = st.session_state.saved_schedules[schedule_name]
    conflicts = []
    
    for i, prog1 in enumerate(programs):
        for j, prog2 in enumerate(programs[i+1:], i+1):
            # Check if same day
            if prog1['Day of the week'] == prog2['Day of the week']:
                start1 = parse_time(prog1['Start time'])
                end1 = parse_time(prog1['End time'])
                start2 = parse_time(prog2['Start time'])
                end2 = parse_time(prog2['End time'])
                
                # Check for time overlap
                if (start1 < end2 and start2 < end1):
                    conflicts.append({
                        'day': prog1['Day of the week'],
                        'program1': prog1['Program Name'],
                        'program2': prog2['Program Name'],
                        'time1': f"{prog1['Start time']} - {prog1['End time']}",
                        'time2': f"{prog2['Start time']} - {prog2['End time']}"
                    })
    
    return conflicts

def filter_programs_by_schedule(filtered_df, schedule_name):
    """Filter programs to show only those in a specific schedule"""
    if schedule_name == "All Programs" or schedule_name not in st.session_state.saved_schedules:
        return filtered_df
    
    # Handle empty dataframe
    if filtered_df.empty:
        return filtered_df
    
    saved_programs = st.session_state.saved_schedules[schedule_name]
    if not saved_programs:  # Handle empty schedule
        return filtered_df.iloc[0:0]  # Return empty dataframe with same structure
    
    saved_program_keys = set()
    
    for prog in saved_programs:
        key = f"{prog['Program Name']}|{prog['Provider Name']}|{prog['Day of the week']}|{prog['Start time']}"
        saved_program_keys.add(key)
    
    # Filter the dataframe to only include saved programs (match by name, provider, day, and time)
    try:
        mask = filtered_df.apply(lambda row: 
            f"{row.get('Program Name', 'N/A')}|{row.get('Provider Name', 'N/A')}|{row.get('Day of the week', 'N/A')}|{row.get('Start time', 'N/A')}" in saved_program_keys, 
            axis=1
        )
        
        # Use .loc to avoid ambiguous boolean indexing
        return filtered_df.loc[mask.fillna(False)]
        
    except Exception as e:
        # If there's an error with filtering, return all programs
        print(f"Error filtering programs: {e}")
        return filtered_df

@st.dialog("📋 Program Details")
def program_details_modal():
    """Show detailed program information with quick actions"""
    program = st.session_state.get('details_program_data')
    if program is None:
        st.error("No program data available")
        return
    
    # Convert pandas Series to dict if needed
    if hasattr(program, 'to_dict'):
        program = program.to_dict()
    
    # Check if it's an empty dict or Series
    if not program or (hasattr(program, 'empty') and program.empty):
        st.error("No program data available")
        return
    
    # Program header - compact
    col1, col2 = st.columns([4, 1])
    with col1:
        category = program.get('Interest Category', 'N/A')
        icon = get_category_icon(category)
        st.markdown(f"### {icon} {program.get('Program Name', 'N/A')}")
        st.markdown(f"{program.get('Provider Name', 'N/A')}")
    
    with col2:
        # Quick save button
        current_schedule = st.session_state.current_schedule
        is_saved = False
        if current_schedule != "All Programs" and current_schedule in st.session_state.saved_schedules:
            prog_name = str(program.get('Program Name', ''))
            prog_provider = str(program.get('Provider Name', ''))
            prog_day = str(program.get('Day of the week', ''))
            prog_time = str(program.get('Start time', ''))
            
            for saved_prog in st.session_state.saved_schedules[current_schedule]:
                if (saved_prog['Program Name'] == prog_name and 
                    saved_prog['Provider Name'] == prog_provider and
                    saved_prog['Day of the week'] == prog_day and
                    saved_prog['Start time'] == prog_time):
                    is_saved = True
                    break
        
        if is_saved:
            if st.button("💖", type="secondary", use_container_width=True, help="Remove from schedule"):
                # Remove from schedule
                st.session_state.saved_schedules[current_schedule] = [
                    p for p in st.session_state.saved_schedules[current_schedule]
                    if not (p['Program Name'] == prog_name and 
                           p['Provider Name'] == prog_provider and
                           p['Day of the week'] == prog_day and
                           p['Start time'] == prog_time)
                ]
                st.success(f"Removed from {current_schedule}")
                st.rerun()
        else:
            if st.button("♡", type="primary", use_container_width=True, help="Save to schedule"):
                st.session_state.popup_program_data = program
                save_program_dialog()
    
    st.markdown("---")
    
    # Program details in two columns
    detail_col1, detail_col2 = st.columns([3, 2])
    
    with detail_col1:
        st.markdown("#### 📅 Schedule Information")
        st.text(f"Day: {program.get('Day of the week', 'N/A')}")
        st.text(f"Time: {program.get('Start time', 'N/A')} - {program.get('End time', 'N/A')}")
        
        age_range = program.get('Age range', '')
        if age_range and not pd.isna(age_range) and str(age_range).strip():
            st.text(f"Ages: {age_range}")
        else:
            min_age_val = program.get('Min Age', 0)
            max_age_val = program.get('Max Age', 0)
            min_age = int(float(min_age_val)) if min_age_val is not None and not pd.isna(min_age_val) and min_age_val != 0 else 0
            max_age = int(float(max_age_val)) if max_age_val is not None and not pd.isna(max_age_val) and max_age_val != 0 else 0
            st.text(f"Ages: {min_age} - {max_age}")
        st.text(f"Category: {program.get('Interest Category', 'N/A')}")
        
        st.markdown("#### 💰 Pricing")
        cost_info = []
        cost = program.get('Cost')
        if cost is not None and not pd.isna(cost):
            enrollment_type = program.get('Enrollment Type', '')
            enrollment_type = enrollment_type.strip() if isinstance(enrollment_type, str) else ''
            base_cost = f"${float(cost):.2f}"
            if enrollment_type:
                if 'semester' in enrollment_type.lower():
                    base_cost += "/semester"
                elif 'monthly' in enrollment_type.lower():
                    base_cost += "/month"
                elif 'drop' in enrollment_type.lower():
                    base_cost += " (drop-in)"
                else:
                    base_cost += f" ({enrollment_type.lower()})"
            cost_info.append(base_cost)
        
        cost_per_class = program.get('Cost Per Class')
        if cost_per_class is not None and not pd.isna(cost_per_class):
            cost_info.append(f"${float(cost_per_class):.2f}/class")
        
        if cost_info:
            st.text(" • ".join(cost_info))
        else:
            st.text("Contact for pricing")
    
    with detail_col2:
        st.markdown("#### 📍 Location & Contact")
        st.text(f"Address: {program.get('Address', 'N/A')}")
        
        contact_phone = program.get('Contact Phone')
        if contact_phone is not None and not pd.isna(contact_phone) and str(contact_phone).strip():
            st.text(f"Phone: {contact_phone}")
        
        website = program.get('Website')
        if website is not None and not pd.isna(website) and str(website).strip():
            st.markdown(f"Website: [Visit Site]({website})")
        
        school_pickup = program.get('School Pickup From')
        if school_pickup is not None and not pd.isna(school_pickup) and str(school_pickup).strip():
            st.markdown("#### 🚌 Transportation")
            st.text(f"School pickup: {school_pickup}")
    
    # Quick action buttons
    st.markdown("---")
    st.markdown("#### Quick Actions")
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("📞", use_container_width=True, help="Call"):
            phone = program.get('Contact Phone')
            if phone and not pd.isna(phone) and str(phone).strip():
                st.success(f"Phone: {phone}")
            else:
                st.warning("No phone number available")
    
    with action_col2:
        if st.button("🗺️", use_container_width=True, help="Get Directions"):
            address = program.get('Address')
            if address and not pd.isna(address) and str(address).strip():
                maps_url = f"https://maps.google.com/maps?q={str(address).replace(' ', '+')}"
                st.markdown(f"[Open in Google Maps]({maps_url})")
            else:
                st.warning("No address available")
    
    with action_col3:
        if st.button("🌐", use_container_width=True, help="Visit Website"):
            website = program.get('Website')
            if website and not pd.isna(website) and str(website).strip():
                st.markdown(f"[Visit Website]({website})")
            else:
                st.warning("No website available")
    
    with action_col4:
        if st.button("✖️", use_container_width=True, help="Close"):
            st.session_state.details_program_data = None
            st.rerun()

@st.dialog("💾 Save Program to Schedule")
def save_program_dialog():
    """Modal dialog for saving programs to schedules"""
    if st.session_state.popup_program_data is None:
        st.error("No program data available")
        return
    
    program = st.session_state.popup_program_data
    program_name = program.get('Program Name', 'N/A')
    
    # Two column layout - wider modal with better proportions
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("### Select Schedule")
        
        # Schedule selection
        existing_schedules = list(st.session_state.saved_schedules.keys())
        schedule_options = ["-- Create New Schedule --"] + existing_schedules
        
        selected_option = st.selectbox(
            "Choose a schedule:",
            options=schedule_options,
            key="modal_schedule_selectbox"
        )
        
        # Schedule name input
        if selected_option == "-- Create New Schedule --":
            schedule_name = st.text_input(
                "Schedule Name:",
                placeholder="e.g., Ami 1, Mia 3, Emma Fall 2024",
                key="modal_schedule_input"
            )
        else:
            schedule_name = selected_option
            st.info(f"Adding to: **{schedule_name}**")
    
    with col2:
        st.markdown("### Program Info")
        category = program.get('Interest Category', 'N/A')
        icon = get_category_icon(category)
        
        # More compact display
        st.markdown(f"**{icon} {program_name}**")
        st.markdown(f"📍 {program.get('Provider Name', 'N/A')}")
        st.markdown(f"📅 {program.get('Day of the week', 'N/A')} | ⏰ {program.get('Start time', 'N/A')} - {program.get('End time', 'N/A')}")
        
        # Additional info on same line when possible
        extra_info = []
        if program.get('Distance', 0) > 0:
            extra_info.append(f"🚗 {program.get('Distance', 0):.1f} miles")
        if program.get('Cost', 0) > 0:
            extra_info.append(f"💰 ${program.get('Cost', 0):.2f}")
        
        if extra_info:
            st.markdown(" | ".join(extra_info))
    
    st.markdown("---")
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("💾 Save", type="primary", use_container_width=True):
            if schedule_name and schedule_name.strip():
                schedule_name_clean = schedule_name.strip()
                
                # Check for duplicate schedule names when creating new schedule
                if selected_option == "-- Create New Schedule --" and schedule_name_clean in st.session_state.saved_schedules:
                    st.error(f"⚠️ Schedule name '{schedule_name_clean}' already exists! Please choose a different name.")
                else:
                    success = add_program_to_schedule(program, schedule_name_clean)
                    if success:
                        st.success(f"✅ Program saved to '{schedule_name_clean}' schedule!")
                        st.session_state.current_schedule = schedule_name_clean
                        
                        # Clear popup state and close modal
                        st.session_state.show_save_popup = False
                        st.session_state.popup_program_data = None
                        st.rerun()
                    else:
                        st.warning("⚠️ Program already exists in this schedule!")
            else:
                st.error("Please enter a schedule name!")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_save_popup = False
            st.session_state.popup_program_data = None
            st.rerun()
    
    with col3:
        if existing_schedules:
            if st.button("🗑️ Manage Schedules", use_container_width=True):
                st.info("Schedule management coming soon!")
                # Could expand this to show schedule management options

def display_schedule_grid(filtered_df):
    """Display programs in a weekly schedule grid with interactive save buttons"""
    if len(filtered_df) == 0:
        return
    
    # Days of the week (Mon-Fri)  
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    # Extract all unique start times from programs
    unique_start_times = set()
    for _, program in filtered_df.iterrows():
        start_time = parse_time(program.get('Start time'))
        if start_time > 0:
            unique_start_times.add(start_time)
    
    # Sort unique start times chronologically
    time_slots = sorted(list(unique_start_times))
    if not time_slots:
        time_slots = [14 * 60 + 30, 15 * 60, 15 * 60 + 30, 16 * 60]
    
    # Group programs by day and start time
    programs_by_day_time = {}
    for day in days:
        programs_by_day_time[day] = {}
        for time_slot in time_slots:
            programs_by_day_time[day][time_slot] = []
    
    # Populate programs into their exact start time slots
    for _, program in filtered_df.iterrows():
        day = program.get('Day of the week', '').strip()
        start_time = parse_time(program.get('Start time'))
        if day in programs_by_day_time and start_time in programs_by_day_time[day]:
            programs_by_day_time[day][start_time].append(program)
    
    # Create interactive schedule using Streamlit components
    
    # Create header row with column widths that account for program + heart button
    header_cols = st.columns([1.0] + [2.0]*len(days))
    with header_cols[0]:
        st.markdown("**Time**")
    for i, day in enumerate(days):
        with header_cols[i+1]:
            st.markdown(f"**{day}**")
    
    st.markdown("---")
    
    # Create rows for each time slot
    for time_slot in time_slots:
        time_str = minutes_to_time_str(time_slot)
        
        # Create columns for this time slot with consistent widths
        time_cols = st.columns([1.0] + [2.0]*len(days))
        
        # Time column
        with time_cols[0]:
            st.markdown(f"**{time_str}**")
        
        # Program columns for each day
        for day_idx, day in enumerate(days):
            with time_cols[day_idx + 1]:
                programs = programs_by_day_time[day][time_slot]
                
                if programs:
                    # Create container for programs at this time/day
                    for i, program in enumerate(programs):
                        program_name = program.get('Program Name', 'N/A')
                        provider_name = program.get('Provider Name', 'N/A')
                        category = program.get('Interest Category', '')
                        distance = program.get('Distance', 0)
                        
                        # Get category icon and distance info
                        icon = get_category_icon(category) 
                        distance_class, distance_text = get_distance_badge_info(distance)
                        
                        # Check if program is saved
                        is_saved = False
                        current_schedule = st.session_state.current_schedule
                        if current_schedule != "All Programs" and current_schedule in st.session_state.saved_schedules:
                            for saved_prog in st.session_state.saved_schedules[current_schedule]:
                                if (saved_prog['Program Name'] == program_name and 
                                    saved_prog['Provider Name'] == provider_name and
                                    saved_prog['Day of the week'] == program.get('Day of the week', '') and
                                    saved_prog['Start time'] == program.get('Start time', '')):
                                    is_saved = True
                                    break
                        
                        # Interactive save/remove button - inline with text
                        button_key = f"heart_{day}_{time_slot}_{i}"
                        heart_symbol = "♥" if is_saved else "♡"
                        
                        # Create inline layout with heart button at the end
                        distance_badge = ""
                        if distance_text:
                            badge_color = "#4CAF50" if "close" in distance_class else "#FF9800" if "medium" in distance_class else "#f44336"
                            distance_badge = f"<span style='font-size: 0.6rem; background: {badge_color}; color: white; padding: 1px 3px; border-radius: 2px; margin-left: 4px;'>{distance_text}</span>"
                        
                        # Determine if program is saved for styling
                        saved_class = "saved" if is_saved else ""
                        
                        # Clickable program card with hover effects
                        card_container = st.container()
                        with card_container:
                            # Add CSS class for styling
                            st.markdown(f'<div class="program-card {saved_class}">', unsafe_allow_html=True)
                            
                            # Make entire card clickable
                            prog_col1, prog_col2 = st.columns([5, 1])
                            with prog_col1:
                                # Clickable program info
                                if st.button(f"{icon} **{program_name}** - {provider_name}", 
                                           key=f"details_{day}_{time_slot}_{i}",
                                           help="Click to view program details",
                                           use_container_width=True):
                                    # Convert pandas Series to dictionary to avoid boolean ambiguity
                                    st.session_state.details_program_data = program.to_dict() if hasattr(program, 'to_dict') else program
                                    program_details_modal()
                            
                            with prog_col2:
                                # Enhanced heart button with visual feedback
                                if is_saved:
                                    if st.button("💖", key=f"remove_{button_key}", help="Remove from schedule"):
                                        if current_schedule in st.session_state.saved_schedules:
                                            st.session_state.saved_schedules[current_schedule] = [
                                                p for p in st.session_state.saved_schedules[current_schedule]
                                                if not (p['Program Name'] == program_name and 
                                                       p['Provider Name'] == provider_name and
                                                       p['Day of the week'] == program.get('Day of the week', '') and
                                                       p['Start time'] == program.get('Start time', ''))
                                            ]
                                            st.success(f"Removed {program_name} from {current_schedule}")
                                            st.rerun()
                                else:
                                    if st.button("♡", key=button_key, help="Save to schedule"):
                                        st.session_state.popup_program_data = program
                                        save_program_dialog()
                            
                            # Close program card div
                            st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        
        st.markdown("---")

# Initialize session state
if 'selected_days' not in st.session_state:
    st.session_state.selected_days = []
if 'selected_interests' not in st.session_state:
    st.session_state.selected_interests = []
if 'child_age' not in st.session_state:
    st.session_state.child_age = 5
if 'start_time' not in st.session_state:
    st.session_state.start_time = "08:00 AM"
if 'end_time' not in st.session_state:
    st.session_state.end_time = "06:00 PM"
if 'user_address' not in st.session_state:
    st.session_state.user_address = ""
if 'max_distance' not in st.session_state:
    st.session_state.max_distance = 1.0
if 'filtered_df' not in st.session_state:
    st.session_state.filtered_df = None
if 'submitted' not in st.session_state:
    st.session_state.submitted = False
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "Schedule View"
if 'saved_schedules' not in st.session_state:
    st.session_state.saved_schedules = {}
if 'current_schedule' not in st.session_state:
    st.session_state.current_schedule = "All Programs"
if 'show_save_popup' not in st.session_state:
    st.session_state.show_save_popup = False
if 'popup_program_data' not in st.session_state:
    st.session_state.popup_program_data = None
if 'save_program_index' not in st.session_state:
    st.session_state.save_program_index = None
if 'details_program_data' not in st.session_state:
    st.session_state.details_program_data = None

# Force light theme CSS - Nuclear Option
st.markdown("""
    <style>
    /* FORCE LIGHT THEME - Override everything */
    .stApp,
    .main,
    [data-testid="stAppViewContainer"],
    .stApp > div,
    .main > div,
    div[data-testid="stAppViewContainer"] > div,
    .block-container,
    [data-testid="block-container"] {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    /* Force all text elements to be dark */
    .stApp *,
    .main *,
    [data-testid="stAppViewContainer"] *,
    p, h1, h2, h3, h4, h5, h6, span, div, label {
        color: #262730 !important;
    }
    
    /* Force form backgrounds */
    .stSelectbox,
    .stMultiSelect,
    .stNumberInput,
    .stTextInput,
    div[data-testid="stForm"],
    .stCheckbox,
    .stButton {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    /* Essential header styling */
    .main-header {
        font-size: 2.2rem !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
        font-weight: 700 !important;
        color: #1E3D59 !important;
    }
    
    /* Program card styling with forced light backgrounds */
    .program-card-container {
        background-color: #f8f9fa !important;
        color: #262730 !important;
        border: 1px solid #e9ecef !important;
        border-radius: 12px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .program-card-title {
        color: #1E3D59 !important;
        font-weight: bold;
        margin-bottom: 0.2rem;
        font-size: 1.2rem;
    }
    
    .program-card-provider {
        color: #1E3D59 !important;
        font-weight: 600;
        margin-bottom: 0.6rem;
        font-size: 1.0rem;
    }
    
    .program-card-info-bar {
        background: #e8f4f8 !important;
        border-radius: 8px;
        padding: 0.7rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid #1E3D59;
    }
    
    .program-card-text {
        margin: 0.2rem 0;
        font-weight: 600;
        color: #1E3D59 !important;
    }
    
    .program-card-secondary {
        margin: 0.4rem 0;
        color: #555 !important;
    }
    
    .program-card-link {
        text-decoration: none;
        color: #1E3D59 !important;
    }
    
    /* Override ANY dark theme detection */
    @media (prefers-color-scheme: dark) {
        .stApp,
        .main,
        [data-testid="stAppViewContainer"],
        .stApp > div,
        .main > div {
            background-color: #FFFFFF !important;
            color: #262730 !important;
        }
    }
    
    /* Override Streamlit's theme classes */
    .stApp[data-theme="dark"],
    [data-testid="stAppViewContainer"][data-theme="dark"] {
        background-color: #FFFFFF !important;
        color: #262730 !important;
    }
    
    .stApp[data-theme="dark"] *,
    [data-testid="stAppViewContainer"][data-theme="dark"] * {
        background-color: inherit !important;
        color: #262730 !important;
    }
    
    /* Fix button contrast with light backgrounds */
    .stButton button {
        background-color: #ffffff !important;
        color: #1E3D59 !important;
        border: 2px solid #1E3D59 !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    .stButton button:hover {
        background-color: #f0f8ff !important;
        border-color: #1E3D59 !important;
        color: #1E3D59 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    
    /* Primary buttons - light background, dark text */
    button[data-testid="baseButton-primary"],
    button[kind="primary"] {
        background-color: #ffffff !important;
        color: #1E3D59 !important;
        border: 2px solid #1E3D59 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }
    
    button[data-testid="baseButton-primary"]:hover,
    button[kind="primary"]:hover {
        background-color: #f0f8ff !important;
        border-color: #1E3D59 !important;
        color: #1E3D59 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    
    /* Secondary buttons - also light background */
    button[data-testid="baseButton-secondary"],
    button[kind="secondary"] {
        background-color: #f8f9fa !important;
        color: #1E3D59 !important;
        border: 2px solid #e9ecef !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
    }
    
    button[data-testid="baseButton-secondary"]:hover,
    button[kind="secondary"]:hover {
        background-color: #e9ecef !important;
        color: #1E3D59 !important;
        border-color: #1E3D59 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.15) !important;
    }
    
    /* Compact program card styling */
    .program-card .stButton button {
        min-height: 24px !important;
        height: 24px !important;
        padding: 2px 6px !important;
        font-size: 0.75rem !important;
        line-height: 1.2 !important;
        text-align: left !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }
    
    /* Make program card buttons more compact and single-line */
    div[data-testid="column"] .stButton button {
        min-height: 24px !important;
        height: 24px !important;
        padding: 2px 6px !important;
        font-size: 0.75rem !important;
        line-height: 1.2 !important;
        text-align: left !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        display: flex !important;
        align-items: center !important;
    }
    
    /* Heart buttons should stay small */
    .program-card .stButton button[title*="Save"],
    .program-card .stButton button[title*="Remove"] {
        min-height: 16px !important;
        height: 16px !important;
        width: 18px !important;
        padding: 0px 2px !important;
        font-size: 0.6rem !important;
    }
    </style>
    
    <script>
    function showProgramDetails(programName) {
        // Create a modal or expand details
        alert('Program Details: ' + programName + '\\n\\nClick functionality implemented!\\nIn a full version, this would show detailed program information.');
    }
    
    function toggleFavorite(event, programData) {
        event.stopPropagation(); // Prevent card click
        
        // Show save to schedule popup
        showSavePopup(programData);
    }
    
    function showSavePopup(programData) {
        // Create popup overlay
        const overlay = document.createElement('div');
        overlay.className = 'save-popup-overlay';
        overlay.onclick = (e) => {
            if (e.target === overlay) closeSavePopup();
        };
        
        // Get existing schedules from Streamlit session state (placeholder)
        const existingSchedules = ['Ami 1', 'Mia 3', 'Emma Fall 2024']; // This would come from session state
        
        // Create popup content
        overlay.innerHTML = `
            <div class="save-popup">
                <h3>Save to Schedule</h3>
                <div class="form-group">
                    <label for="schedule-select">Select Schedule:</label>
                    <select id="schedule-select">
                        <option value="">-- Create New Schedule --</option>
                        ${existingSchedules.map(schedule => `<option value="${schedule}">${schedule}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label for="schedule-name">Schedule Name:</label>
                    <input type="text" id="schedule-name" placeholder="e.g., Ami 1, Mia 3, Emma Fall 2024" />
                </div>
                <div class="save-popup-actions">
                    <button class="btn-secondary" onclick="closeSavePopup()">Cancel</button>
                    <button class="btn-primary" onclick="saveToSchedule('${programData}')">Save Program</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Handle schedule selection
        const select = document.getElementById('schedule-select');
        const nameInput = document.getElementById('schedule-name');
        
        select.onchange = () => {
            if (select.value) {
                nameInput.value = select.value;
                nameInput.disabled = true;
            } else {
                nameInput.value = '';
                nameInput.disabled = false;
                nameInput.focus();
            }
        };
    }
    
    function closeSavePopup() {
        const overlay = document.querySelector('.save-popup-overlay');
        if (overlay) {
            overlay.remove();
        }
    }
    
    function saveToSchedule(programData) {
        const scheduleName = document.getElementById('schedule-name').value.trim();
        
        if (!scheduleName) {
            alert('Please enter a schedule name');
            return;
        }
        
        // In a full implementation, this would update Streamlit session state
        console.log('Saving program to schedule:', scheduleName, programData);
        
        // Show success message
        alert(`Program saved to "${scheduleName}" schedule!\\n\\nIn a full version, this would:\\n- Update the session state\\n- Add conflict detection\\n- Refresh the schedule view`);
        
        closeSavePopup();
    }
    
    function switchSchedule(scheduleName) {
        console.log('Switching to schedule:', scheduleName);
        // This would trigger a Streamlit rerun with the new schedule
    }
    
    function deleteSchedule(scheduleName) {
        if (confirm(`Are you sure you want to delete the "${scheduleName}" schedule?`)) {
            console.log('Deleting schedule:', scheduleName);
            // This would update session state and rerun
        }
    }
    
    function duplicateSchedule(scheduleName) {
        const newName = prompt(`Enter name for duplicate of "${scheduleName}":`, scheduleName + ' Copy');
        if (newName && newName.trim()) {
            console.log('Duplicating schedule:', scheduleName, 'to', newName.trim());
            // This would update session state and rerun
        }
    }
    
    function renameSchedule(scheduleName) {
        const newName = prompt(`Enter new name for "${scheduleName}":`, scheduleName);
        if (newName && newName.trim() && newName.trim() !== scheduleName) {
            console.log('Renaming schedule:', scheduleName, 'to', newName.trim());
            // This would update session state and rerun
        }
    }
    </script>
""", unsafe_allow_html=True)

# App header
st.markdown("<h1 class='main-header' style='font-size: 2.2rem; color: #1E3D59 !important; text-align: center; margin-bottom: 2rem; line-height: 1.2; white-space: nowrap; font-weight: 700;'>📚 Find Perfect After-School Programs</h1>", unsafe_allow_html=True)

# Load data
try:
    df = load_and_process_data("attached_assets/ProgramData.csv")
    
    # Get unique values for filters
    interest_categories = get_unique_values(df, 'Interest Category')
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Create time options
    time_options = []
    for am_pm in ["AM", "PM"]:
        time_options.append(f"12:00 {am_pm}")
        for h in range(1, 12):
            time_options.append(f"{h:02d}:00 {am_pm}")

    # Create form with improved organization
    with st.form(key='program_filter_form'):
        # Child Information Section
        st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #1E3D59; margin: 1.5rem 0 0.75rem 0; border-bottom: 2px solid #e9ecef; padding-bottom: 0.5rem;">👶 Child Information</div>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            child_age = st.number_input(
                "Child's Age",
                min_value=0,
                max_value=18,
                value=st.session_state.child_age,
                help="Enter your child's age to find age-appropriate programs"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
        
        # Program Interests
        st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #1E3D59; margin: 1.5rem 0 0.75rem 0; border-bottom: 2px solid #e9ecef; padding-bottom: 0.5rem;">🎨 Program Interests</div>', unsafe_allow_html=True)
        selected_interests = st.multiselect(
            "What activities interest your child?",
            options=interest_categories,
            default=st.session_state.selected_interests,
            help="Select one or more categories that match your child's interests"
        )
        
        # Location & Distance Section
        st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #1E3D59; margin: 1.5rem 0 0.75rem 0; border-bottom: 2px solid #e9ecef; padding-bottom: 0.5rem;">📍 Location & Distance</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            user_address = st.text_input(
                "Your Address (Optional)",
                value=st.session_state.user_address,
                placeholder="123 Main St, Brooklyn, NY",
                help="Enter your address to see distances and get a personalized map view"
            )
        with col2:
            max_distance = st.number_input(
                "Max Distance (miles)",
                min_value=0.1,
                max_value=100.0,
                value=float(st.session_state.max_distance),
                step=0.5,
                help="Maximum distance you're willing to travel"
            )
        
        # Schedule Preferences Section
        st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #1E3D59; margin: 1.5rem 0 0.75rem 0; border-bottom: 2px solid #e9ecef; padding-bottom: 0.5rem;">⏰ Schedule Preferences</div>', unsafe_allow_html=True)
        
        time_col1, time_col2 = st.columns(2)
        with time_col1:
            start_time = st.selectbox(
                "Earliest Start Time",
                options=time_options,
                index=time_options.index(st.session_state.start_time),
                help="Programs should start no earlier than this time"
            )
        with time_col2:
            end_time_index = time_options.index(st.session_state.end_time) if st.session_state.end_time in time_options else len(time_options) - 1
            end_time = st.selectbox(
                "Latest End Time",
                options=time_options,
                index=end_time_index,
                help="Programs should end no later than this time"
            )
        
        # Days of week - improved mobile-friendly selection
        st.markdown('<div style="font-size: 1.1rem; font-weight: 600; color: #1E3D59; margin: 1.5rem 0 0.75rem 0; border-bottom: 2px solid #e9ecef; padding-bottom: 0.5rem;">📅 Days Available</div>', unsafe_allow_html=True)
        st.markdown("Select the days your child is available for programs:")
        
        # Create a more mobile-friendly day selection interface
        selected_days = []
        day_cols = st.columns(4)  # 4 columns for better mobile layout
        
        for i, day in enumerate(days_of_week):
            col_index = i % 4
            with day_cols[col_index]:
                is_selected = day in st.session_state.selected_days
                if st.checkbox(
                    day, 
                    value=is_selected, 
                    key=f"day_{day}"
                ):
                    selected_days.append(day)
        
        # Submit button with better styling
        st.markdown('<div class="submit-section">', unsafe_allow_html=True)
        st.markdown("**Ready to find programs?**")
        submitted = st.form_submit_button(label="🔍 Find Perfect Programs", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if submitted:
            # Update session state
            st.session_state.child_age = child_age
            st.session_state.selected_interests = selected_interests
            st.session_state.selected_days = selected_days
            st.session_state.start_time = start_time
            st.session_state.end_time = end_time
            st.session_state.user_address = user_address
            st.session_state.max_distance = max_distance
            st.session_state.submitted = True
            
            # Filter programs
            filters = {
                'child_age': child_age,
                'selected_interests': selected_interests,
                'selected_days': selected_days,
                'start_time': start_time,
                'end_time': end_time,
                'user_address': user_address,
                'max_distance': max_distance
            }
            
            filtered_df = filter_programs(df, filters)
            st.session_state.filtered_df = filtered_df

    # Show results if form was submitted
    if st.session_state.submitted and st.session_state.filtered_df is not None:
        filtered_df = st.session_state.filtered_df
        
        # Show number of results with better styling
        result_text = f"🎉 Found {len(filtered_df)} programs matching your criteria!"
        if len(filtered_df) == 0:
            result_text = "😔 No programs found matching your criteria. Try adjusting your filters."
        elif len(filtered_df) == 1:
            result_text = "🎉 Found 1 perfect program for your child!"
        
        st.markdown(f"""
        <style>
        .result-count-text {{
            color: #1E3D59 !important;
            font-size: 1.4rem !important;
            margin: 1rem 0 0.5rem 0 !important;
            text-align: center !important;
            padding: 0.5rem !important;
            font-weight: 600 !important;
        }}
        </style>
        <div class="result-count-text">{result_text}</div>
        """, unsafe_allow_html=True)
        
        # Top Navigation Bar
        if len(filtered_df) > 0:
            st.markdown('<div style="padding: 0.5rem 0; margin: 1rem 0;">', unsafe_allow_html=True)
            
            # Improved navigation layout - Option 3
            nav_col1, nav_col2, nav_spacer, nav_col3 = st.columns([2, 2, 1, 3])
            
            # View mode buttons (left side)
            with nav_col1:
                if st.button("🗓️ Schedule View", key="schedule_view", 
                           type="primary" if st.session_state.view_mode == "Schedule View" else "secondary",
                           use_container_width=True):
                    st.session_state.view_mode = "Schedule View"
            
            with nav_col2:
                if st.button("📋 List View", key="list_view",
                           type="primary" if st.session_state.view_mode == "List View" else "secondary", 
                           use_container_width=True):
                    st.session_state.view_mode = "List View"
            
            # Schedule selection dropdown (right side)
            with nav_col3:
                schedule_names = ["All Programs"] + list(st.session_state.saved_schedules.keys())
                
                # Find current schedule index
                try:
                    current_index = schedule_names.index(st.session_state.current_schedule)
                except ValueError:
                    current_index = 0  # Default to "All Programs"
                
                # Create dropdown for schedule selection
                selected_schedule = st.selectbox(
                    "Show:",
                    options=schedule_names,
                    index=current_index,
                    key="schedule_dropdown",
                    help="Select which schedule to display"
                )
                
                # Update current schedule if changed
                if selected_schedule != st.session_state.current_schedule:
                    st.session_state.current_schedule = selected_schedule
                    st.rerun()
            
            
            # Show conflicts if any
            current_schedule_display = st.session_state.current_schedule
            if current_schedule_display != "All Programs":
                conflicts = detect_schedule_conflicts(current_schedule_display)
                if conflicts:
                    st.markdown("---")
                    conflict_text = f"⚠️ {len(conflicts)} scheduling conflicts detected in {current_schedule_display}"
                    st.warning(conflict_text)
                    
                    for conflict in conflicts:
                        st.error(f"**{conflict['day']}**: {conflict['program1']} ({conflict['time1']}) overlaps with {conflict['program2']} ({conflict['time2']})")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Filter programs by current schedule
            display_df = filter_programs_by_schedule(filtered_df, st.session_state.current_schedule)
            
            # Update filtered_df for display
            filtered_df = display_df
        
        # Create map with program locations
        if len(filtered_df) > 0:
            # Get coordinates for all programs
            program_coords = []
            for _, program in filtered_df.iterrows():
                prog_coords = geocode_address(program['Address'])
                if prog_coords:
                    program_coords.append((prog_coords, program))
            
            if program_coords:
                # Calculate bounds for auto-zoom
                lats = [coord[0] for coord, _ in program_coords]
                lons = [coord[1] for coord, _ in program_coords]
                
                # Add user location to bounds if available
                user_coords = None
                if st.session_state.user_address:
                    user_coords = geocode_address(st.session_state.user_address)
                    if user_coords:
                        lats.append(user_coords[0])
                        lons.append(user_coords[1])
                
                # Calculate center and create map
                center_lat = sum(lats) / len(lats)
                center_lon = sum(lons) / len(lons)
                
                m = folium.Map(location=[center_lat, center_lon])
                
                # Fit bounds to show all markers with padding
                if len(program_coords) >= 1:
                    if len(lats) > 1:  # Multiple points
                        southwest = [min(lats), min(lons)]
                        northeast = [max(lats), max(lons)]
                        m.fit_bounds([southwest, northeast], padding=(20, 20))
                    else:  # Single point - set a reasonable zoom level
                        m = folium.Map(location=[center_lat, center_lon], zoom_start=14)
                
                # Add user marker if address is provided and geocoding succeeded
                if st.session_state.user_address:
                    user_coords = geocode_address(st.session_state.user_address)
                    if user_coords:
                        folium.Marker(
                            user_coords,
                            popup="Your Location",
                            icon=folium.Icon(color="red", icon="home", prefix="fa"),
                        ).add_to(m)
                
                # Add program markers
                for prog_coords, program in program_coords:
                    # Create popup with distance if available
                    if 'Distance' in program and not pd.isna(program['Distance']):
                        popup_html = f"""
                        <strong>{program['Program Name']}</strong><br>
                        {program['Provider Name']}<br>
                        Distance: {program['Distance']:.2f} miles
                        """
                    else:
                        popup_html = f"""
                        <strong>{program['Program Name']}</strong><br>
                        {program['Provider Name']}<br>
                        {program['Address']}
                        """
                    folium.Marker(
                        prog_coords,
                        popup=popup_html,
                        icon=folium.Icon(color="blue", icon="info-circle", prefix="fa"),
                    ).add_to(m)
                
                # Show map for both views
                st.markdown("""
                <style>
                .map-header {
                    font-size: 1.3rem !important;
                    font-weight: 600 !important;
                    color: #1E3D59 !important;
                    margin: 0.2rem 0 0.2rem 0 !important;
                    padding: 0 !important;
                }
                </style>
                <div class="map-header">🗺️ Program Locations</div>
                """, unsafe_allow_html=True)
                
                # Responsive map sizing
                map_container = st.container()
                with map_container:
                    st_folium(m, width="100%", height=400, use_container_width=True)
        
        # Display results based on view mode
        if len(filtered_df) > 0:
            if st.session_state.view_mode == "List View":
                # List View
                st.markdown("""
                <style>
                .list-view-header {
                    font-size: 1.3rem !important;
                    font-weight: 600 !important;
                    color: #1E3D59 !important;
                    margin: 0.2rem 0 !important;
                    padding: 0 !important;
                }
                </style>
                <div class="list-view-header">📋 Program Details</div>
                """, unsafe_allow_html=True)
                for _, program in filtered_df.iterrows():
                    display_program_card(program)
            else:
                # Schedule View
                st.markdown("""
                <style>
                .schedule-view-header {
                    font-size: 1.3rem !important;
                    font-weight: 600 !important;
                    color: #1E3D59 !important;
                    margin: 0.2rem 0 !important;
                    padding: 0 !important;
                }
                .schedule-instruction {
                    font-size: 0.9rem !important;
                    color: #666 !important;
                    margin: 0.2rem 0 1rem 0 !important;
                    font-style: italic !important;
                }
                </style>
                <div class="schedule-view-header">📅 Weekly Schedule</div>
                <div class="schedule-instruction">Click ♡ to save programs to your schedule</div>
                """, unsafe_allow_html=True)
                display_schedule_grid(filtered_df)
        else:
            st.info("💡 **Tips for better results:**\n- Try increasing the distance range\n- Select fewer interest categories\n- Adjust the time range\n- Check more days of the week")
        
        # Modal dialogs are triggered by button clicks and handled by @st.dialog decorator
        if st.session_state.get('details_program_data'):
            program_details_modal()
    
except Exception as e:
    st.error(f"Error: {str(e)}")
