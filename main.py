import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from datetime import datetime
import time
from utils import filter_programs, geocode_address, load_and_process_data, get_unique_values, get_category_icon, get_distance_badge_info, get_availability_status

# Force light theme configuration
st.set_page_config(
    page_title="After-School Finder",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile-Optimized Button Alignment System
st.markdown("""
<style>
/* Mobile-first button alignment system */
/* Minimum touch target size: 44x44px with proper spacing */

/* PRIMARY ACTION BUTTONS - Centered for prominence */
.primary-action button {
    min-height: 44px !important;
    margin: 10px 0 !important;
    display: block !important;
    margin-left: auto !important;
    margin-right: auto !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    color: white !important;
    font-size: 1rem !important;
}

/* SECONDARY ACTION BUTTONS - Standard alignment */
.secondary-action button {
    min-height: 44px !important;
    margin: 8px 0 !important;
    border-radius: 6px !important;
    padding: 10px 16px !important;
    font-size: 0.9rem !important;
}

/* GRID/LIST BUTTONS - Left aligned for natural reading */
.grid-button {
    text-align: left !important;
    min-height: 44px !important;
    margin: 4px 0 !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
    border: 1px solid #e9ecef !important;
    background: white !important;
    position: relative !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
}

.grid-button button {
    text-align: left !important;
    min-height: 44px !important;
    width: 100% !important;
    padding: 12px 16px !important;
    border-radius: 6px !important;
    font-size: 0.9rem !important;
    line-height: 1.3 !important;
    background: white !important;
    border: 1px solid #dee2e6 !important;
    color: #333 !important;
    transition: all 0.2s ease !important;
}

.grid-button button:hover {
    background: #f8f9fa !important;
    border-color: #adb5bd !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
}

/* PROGRAM BUTTONS WITH HEART ICONS - Force tight spacing */
.program-button {
    position: relative !important;
    min-height: 38px !important;
    margin: 1px 0 !important; /* Very tight spacing for desktop */
    padding: 0 !important;
}

/* Target Streamlit's button container specifically */
.program-button > div {
    margin: 0 !important;
    padding: 0 !important;
}

.program-button button {
    text-align: left !important;
    width: 100% !important;
    min-height: 38px !important;
    height: 38px !important; /* Force specific height */
    padding: 6px 40px 6px 12px !important; /* Reduced padding */
    border-radius: 4px !important;
    background: white !important;
    border: 1px solid #dee2e6 !important;
    color: #333 !important;
    font-size: 0.85rem !important;
    line-height: 1.2 !important;
    transition: all 0.2s ease !important;
    margin: 0 !important; /* Force no margin */
}

/* Target Streamlit's default spacing - multiple approaches */
div[data-testid="column"] > div > div:has(.program-button) {
    margin: 1px 0 !important;
    padding: 0 !important;
}

/* Force tight spacing on Streamlit's element containers */
.element-container:has(.program-button) {
    margin-top: 1px !important;
    margin-bottom: 1px !important;
    padding: 0 !important;
}

/* Alternative targeting for Streamlit containers */
div[data-testid="stVerticalBlock"] > div:has(.program-button) {
    margin: 1px 0 !important;
    padding: 0 !important;
}

/* Nuclear option - force all buttons in columns to be tight */
div[data-testid="column"] button {
    margin: 2px 0 !important;
}

.program-button button:hover {
    background: #f8f9fa !important;
    border-color: #adb5bd !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
}

/* FAVORITE HEART ICON - Right aligned within button */
.favorite-heart {
    position: absolute !important;
    right: 10px !important; /* Closer to edge for tighter layout */
    top: 50% !important;
    transform: translateY(-50%) !important;
    font-size: 1rem !important; /* Slightly smaller for desktop */
    color: #dc3545 !important;
    cursor: pointer !important;
    z-index: 2 !important;
    min-width: 20px !important; /* Smaller for desktop */
    min-height: 20px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

/* ACTION BUTTONS IN MODALS - Centered with spacing */
.modal-actions {
    margin-top: 20px !important;
    display: flex !important;
    gap: 10px !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
}

.modal-actions button {
    min-height: 44px !important;
    min-width: 120px !important;
    margin: 5px !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
}

/* NAVIGATION BUTTONS - Clean minimal style */
.nav-button button {
    min-height: 44px !important;
    padding: 10px 20px !important;
    border-radius: 6px !important;
    margin: 5px 0 !important;
    font-size: 0.9rem !important;
}

/* MOBILE RESPONSIVE ADJUSTMENTS */
@media (max-width: 768px) {
    .primary-action button {
        font-size: 0.95rem !important;
        padding: 14px 20px !important;
        min-height: 48px !important;
    }
    
    .grid-button button, .program-button button {
        min-height: 48px !important;
        padding: 12px 16px !important;
        font-size: 0.9rem !important;
        line-height: 1.3 !important;
    }
    
    .program-button {
        margin: 4px 0 !important; /* More spacing on mobile for touch targets */
    }
    
    .program-button button {
        padding: 12px 44px 12px 16px !important; /* More space for heart on mobile */
    }
    
    .favorite-heart {
        right: 14px !important;
        min-width: 28px !important;
        min-height: 28px !important;
        font-size: 1.2rem !important;
    }
    
    .modal-actions {
        flex-direction: column !important;
        align-items: stretch !important;
    }
    
    .modal-actions button {
        width: 100% !important;
        min-height: 48px !important;
        margin: 4px 0 !important;
    }
}

/* TOUCH TARGET SAFETY */
button, .favorite-heart {
    touch-action: manipulation !important;
    -webkit-tap-highlight-color: rgba(0,0,0,0.1) !important;
}

/* BUTTON SPACING SYSTEM */
.button-group {
    margin: 10px 0 !important;
}

.button-row {
    margin: 8px 0 !important;
}

.button-spacing {
    margin: 6px 0 !important;
}
</style>
""", unsafe_allow_html=True)

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
        'Cost Per Class': program.get('Cost Per Class', 0),
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
    """Filter programs to show only those in a specific schedule or Family View"""
    if schedule_name == "All Programs":
        return filtered_df
    
    # Handle Family View - combine all saved schedules
    if schedule_name == "Family View":
        if not st.session_state.saved_schedules:
            return filtered_df.iloc[0:0]  # Return empty dataframe
        
        # Collect all programs from all schedules with schedule labels
        family_programs = []
        for sched_name, programs in st.session_state.saved_schedules.items():
            for prog in programs:
                # Add schedule name to program data for Family View
                prog_with_schedule = prog.copy()
                prog_with_schedule['Schedule_Name'] = sched_name
                family_programs.append(prog_with_schedule)
        
        if not family_programs:
            return filtered_df.iloc[0:0]
        
        # Create DataFrame from family programs
        family_df = pd.DataFrame(family_programs)
        
        # Filter original dataframe to match family programs
        saved_program_keys = set()
        for prog in family_programs:
            key = f"{prog['Program Name']}|{prog['Provider Name']}|{prog['Day of the week']}|{prog['Start time']}"
            saved_program_keys.add(key)
        
        try:
            mask = filtered_df.apply(lambda row: 
                f"{row.get('Program Name', 'N/A')}|{row.get('Provider Name', 'N/A')}|{row.get('Day of the week', 'N/A')}|{row.get('Start time', 'N/A')}" in saved_program_keys, 
                axis=1
            )
            
            result_df = filtered_df.loc[mask.fillna(False)].copy()
            
            # Add schedule names to the result dataframe
            if not result_df.empty:
                result_df['Schedule_Name'] = result_df.apply(lambda row: 
                    next((prog['Schedule_Name'] for prog in family_programs 
                          if (prog['Program Name'] == row.get('Program Name', 'N/A') and 
                              prog['Provider Name'] == row.get('Provider Name', 'N/A') and
                              prog['Day of the week'] == row.get('Day of the week', 'N/A') and
                              prog['Start time'] == row.get('Start time', 'N/A'))), ''), 
                    axis=1
                )
            
            return result_df
            
        except Exception as e:
            print(f"Error filtering family programs: {e}")
            return filtered_df.iloc[0:0]
    
    # Handle individual schedule
    if schedule_name not in st.session_state.saved_schedules:
        return filtered_df.iloc[0:0]
    
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
    
    # Program header with enhanced visual information
    col1, col2 = st.columns([4, 1])
    with col1:
        category = program.get('Interest Category', 'N/A')
        icon = get_category_icon(category)
        distance = program.get('Distance', 0)
        distance_class, distance_text = get_distance_badge_info(distance)
        availability_status, availability_color = get_availability_status(program)
        
        st.markdown(f"### {icon} {program.get('Program Name', 'N/A')}")
        st.markdown(f"{program.get('Provider Name', 'N/A')}")
        
        # Show visual badges in the modal header
        badges_html = ""
        if distance_text:
            badge_color = "#28a745" if distance_class == "close" else "#ffc107" if distance_class == "medium" else "#dc3545"
            badges_html += f'<span style="font-size: 0.8rem; background: {badge_color}; color: white; padding: 3px 8px; border-radius: 12px; margin-right: 6px;">{distance_text}</span>'
        
        if availability_status:
            badges_html += f'<span style="font-size: 0.8rem; background: {availability_color}; color: white; padding: 3px 8px; border-radius: 12px; margin-right: 6px;">{availability_status}</span>'
        
        if badges_html:
            st.markdown(badges_html, unsafe_allow_html=True)
    
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
            if st.button("💖 Saved", type="secondary", use_container_width=True):
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
            if st.button("💾 Save", type="primary", use_container_width=True):
                st.session_state.popup_program_data = program
                st.session_state.show_save_dialog = True
                st.session_state.show_program_details = False  # Close details modal
                st.rerun()
    
    st.markdown("---")
    
    # Program details in two columns
    detail_col1, detail_col2 = st.columns([3, 2])
    
    with detail_col1:
        st.markdown("#### 📅 Schedule Information")
        st.text(f"Day: {program.get('Day of the week', 'N/A')}")
        st.text(f"Time: {program.get('Start time', 'N/A')} - {program.get('End time', 'N/A')}")
        
        age_range = program.get('Age range', '')
        # Safe boolean check to avoid pandas Series ambiguity
        if age_range is not None and not pd.isna(age_range) and str(age_range).strip():
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
    
    # Quick action buttons with mobile-optimized styling
    st.markdown("---")
    st.markdown("#### Quick Actions")
    
    # Modal action buttons with proper mobile alignment
    st.markdown('<div class="modal-actions">', unsafe_allow_html=True)
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("📞 Call", use_container_width=True, help="Call program"):
            phone = program.get('Contact Phone')
            if phone is not None and not pd.isna(phone) and str(phone).strip():
                st.success(f"Phone: {phone}")
            else:
                st.warning("No phone number available")
    
    with action_col2:
        if st.button("🗺️ Map", use_container_width=True, help="Get directions"):
            address = program.get('Address')
            if address is not None and not pd.isna(address) and str(address).strip():
                maps_url = f"https://maps.google.com/maps?q={str(address).replace(' ', '+')}"
                st.markdown(f"[Open in Google Maps]({maps_url})")
            else:
                st.warning("No address available")
    
    with action_col3:
        if st.button("🌐 Web", use_container_width=True, help="Visit website"):
            website = program.get('Website')
            if website is not None and not pd.isna(website) and str(website).strip():
                st.markdown(f"[Visit Website]({website})")
            else:
                st.warning("No website available")
    
    with action_col4:
        if st.button("✖️ Close", use_container_width=True, help="Close details"):
            st.session_state.details_program_data = None
            st.session_state.show_program_details = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

@st.dialog("💾 Save Program to Schedule")
def save_program_dialog():
    """Enhanced modal dialog for saving programs to schedules with smooth UX"""
    if st.session_state.popup_program_data is None:
        st.error("No program data available")
        return
    
    program = st.session_state.popup_program_data
    program_name = program.get('Program Name', 'N/A')
    
    # Add CSS for smooth dialog transitions and mobile optimization
    st.markdown("""
    <style>
    /* Enhanced save dialog styling */
    .save-dialog-container {
        animation: slideInFromTop 0.3s ease-out;
    }
    
    @keyframes slideInFromTop {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Mobile-optimized text input */
    .stTextInput input {
        min-height: 44px !important;
        font-size: 16px !important; /* Prevents zoom on iOS */
        padding: 12px 16px !important;
        border-radius: 8px !important;
        border: 2px solid #e9ecef !important;
    }
    
    .stTextInput input:focus {
        border-color: #1E3D59 !important;
        box-shadow: 0 0 0 3px rgba(30, 61, 89, 0.1) !important;
    }
    
    /* Success animation */
    .save-success {
        animation: successPulse 0.6s ease-out;
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
        color: white !important;
        padding: 15px 20px !important;
        border-radius: 12px !important;
        text-align: center !important;
        font-weight: 600 !important;
        margin: 10px 0 !important;
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3) !important;
    }
    
    @keyframes successPulse {
        0% { opacity: 0; transform: scale(0.9); }
        50% { transform: scale(1.05); }
        100% { opacity: 1; transform: scale(1); }
    }
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .stTextInput input {
            min-height: 48px !important;
            font-size: 16px !important;
        }
        
        /* Hint messages mobile optimization */
        div[style*="background: #fff3cd"], div[style*="background: #d1edff"] {
            margin: 8px -10px !important;
            padding: 12px 15px !important;
            border-radius: 8px !important;
            font-size: 0.9rem !important;
            line-height: 1.4 !important;
        }
    }
    </style>
    <div class="save-dialog-container">
    """, unsafe_allow_html=True)
    
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
        
        # Schedule name input with dynamic contextual help and smart defaults
        if selected_option == "-- Create New Schedule --":
            # Use last used schedule name as default if available
            default_value = st.session_state.last_schedule_name if st.session_state.last_schedule_name else ""
            
            schedule_name = st.text_input(
                "Schedule Name:",
                value=default_value,
                placeholder="Your child's name (e.g., Ami, Mia, Emma)",
                key="modal_schedule_input",
                help="💡 Tip: Press Enter to save quickly!"
            )
            
            # Dynamic contextual help based on user input
            if schedule_name:
                schedule_lower = schedule_name.lower().strip()
                
                # Check for generic/poor naming patterns
                generic_patterns = ['schedule', 'test', 'temp', 'new', 'untitled', 'draft']
                if any(pattern in schedule_lower for pattern in generic_patterns) or schedule_lower.isdigit():
                    st.markdown("""
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 8px 12px; margin-top: 5px;">
                        <span style="color: #856404;">💡 <strong>Tip:</strong> Consider using your child's name like "Emma" - it's much easier to remember and find later!</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Check for numbers/dates
                elif any(char.isdigit() for char in schedule_name) and not any(char.isalpha() for char in schedule_name):
                    st.markdown("""
                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 8px 12px; margin-top: 5px;">
                        <span style="color: #856404;">💡 <strong>Suggestion:</strong> Try your child's name instead - much easier to find later!</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Check for good naming (looks like a name)
                elif (len(schedule_name) >= 2 and 
                      schedule_name[0].isupper() and 
                      schedule_name.replace(' ', '').replace('-', '').isalpha() and
                      len(schedule_name.split()) <= 3):
                    st.markdown("""
                    <div style="background: #d1edff; border: 1px solid #74c0fc; border-radius: 6px; padding: 8px 12px; margin-top: 5px;">
                        <span style="color: #0c5460;">✅ <strong>Great choice!</strong> Easy to identify and remember later.</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Check for mixed patterns (name + something else - still good)
                elif (len(schedule_name) >= 2 and 
                      schedule_name[0].isupper() and 
                      any(char.isalpha() for char in schedule_name) and
                      not any(pattern in schedule_lower for pattern in generic_patterns)):
                    st.markdown("""
                    <div style="background: #d1edff; border: 1px solid #74c0fc; border-radius: 6px; padding: 8px 12px; margin-top: 5px;">
                        <span style="color: #0c5460;">👍 <strong>Good!</strong> Including your child's name makes it easy to find.</span>
                    </div>
                    """, unsafe_allow_html=True)
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
    
    # Show success message if available
    if st.session_state.save_success_message:
        st.markdown(f'<div class="save-success">✅ {st.session_state.save_success_message}</div>', unsafe_allow_html=True)
        # Clear success message after showing it
        st.session_state.save_success_message = ""
    
    st.markdown("---")
    
    # Action buttons with mobile-optimized styling and Enter key support
    st.markdown('<div class="modal-actions">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # Check if Enter key was pressed (simulate by checking if schedule name changed and is complete)
    save_triggered = False
    
    with col1:
        if st.button("💾 Save", type="primary", use_container_width=True):
            save_triggered = True
    
    # Handle save action (either button click or Enter key)
    if save_triggered:
        if schedule_name and schedule_name.strip():
            schedule_name_clean = schedule_name.strip()
            
            # Check for duplicate schedule names when creating new schedule
            if selected_option == "-- Create New Schedule --" and schedule_name_clean in st.session_state.saved_schedules:
                st.error(f"⚠️ Schedule name '{schedule_name_clean}' already exists! Please choose a different name.")
            else:
                success = add_program_to_schedule(program, schedule_name_clean)
                if success:
                    # Remember this schedule name for next time
                    st.session_state.last_schedule_name = schedule_name_clean
                    
                    # Set success message
                    st.session_state.save_success_message = f"Saved to {schedule_name_clean}!"
                    st.session_state.current_schedule = schedule_name_clean
                    
                    # Clear popup state and close modal with smooth transition
                    st.session_state.show_save_popup = False
                    st.session_state.show_save_dialog = False
                    st.session_state.popup_program_data = None
                    
                    # Add a brief success message in main app
                    st.success(f"✅ {program_name} saved to '{schedule_name_clean}' schedule!", icon="🎉")
                    st.rerun()
                else:
                    st.warning("⚠️ Program already exists in this schedule!")
        else:
            st.error("Please enter a schedule name!")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_save_popup = False
            st.session_state.show_save_dialog = False
            st.session_state.popup_program_data = None
            st.rerun()
    
    with col3:
        if existing_schedules:
            if st.button("🗑️ Manage", use_container_width=True):
                st.info("Schedule management coming soon!")
                # Could expand this to show schedule management options
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Close the save dialog container
    st.markdown('</div>', unsafe_allow_html=True)

# Removed alternative grid functions - keeping only standard view

def display_schedule_grid(filtered_df):
    """Display programs in a weekly schedule grid with interactive save buttons (ORIGINAL VERSION)"""
    if len(filtered_df) == 0:
        return
        
    # No header needed - keeping it clean
    
    # Add CSS for visual indicators
    st.markdown("""
    <style>
    .schedule-selected {
        border-left: 3px solid #28a745 !important;
        background: rgba(40, 167, 69, 0.05) !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
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
    
    # Create interactive schedule using Streamlit components with sticky header
    
    # Clean, non-sticky schedule headers
    st.markdown("""
    <style>
    /* Clean schedule headers - no sticky positioning */
    .schedule-day-header {
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        color: #1E3D59 !important;
        text-align: center !important;
        padding: 12px 8px !important;
        background: #f8f9fa !important;
        border-radius: 8px !important;
        border: 1px solid #e9ecef !important;
        margin-bottom: 10px !important;
    }
    
    .schedule-time-header {
        font-weight: 700 !important;
        font-size: 1rem !important;
        color: #1E3D59 !important;
        text-align: center !important;
        padding: 12px 8px !important;
        background: #f8f9fa !important;
        border-radius: 8px !important;
        border: 1px solid #e9ecef !important;
        margin-bottom: 10px !important;
    }
    
    /* Mobile responsive adjustments */
    @media (max-width: 768px) {
        .schedule-day-header, .schedule-time-header {
            font-size: 0.9rem !important;
            padding: 8px 4px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Clean header row with enhanced styling
    header_cols = st.columns([1.0] + [2.0]*len(days))
    with header_cols[0]:
        st.markdown('<div class="schedule-time-header">Time</div>', unsafe_allow_html=True)
    for i, day in enumerate(days):
        with header_cols[i+1]:
            st.markdown(f'<div class="schedule-day-header">{day}</div>', unsafe_allow_html=True)
    
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
                        
                        # Get enhanced visual information using utils functions
                        icon = get_category_icon(category) 
                        distance_class, distance_text = get_distance_badge_info(distance)
                        availability_status, availability_color = get_availability_status(program)
                        
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
                        
                        # Create visual badges for distance and availability
                        badges_html = ""
                        if distance_text:
                            badge_color = "#28a745" if distance_class == "close" else "#ffc107" if distance_class == "medium" else "#dc3545"
                            badges_html += f'<span style="font-size: 0.7rem; background: {badge_color}; color: white; padding: 2px 6px; border-radius: 10px; margin-left: 4px;">{distance_text}</span>'
                        
                        if availability_status:
                            badges_html += f'<span style="font-size: 0.7rem; background: {availability_color}; color: white; padding: 2px 6px; border-radius: 10px; margin-left: 4px;">{availability_status}</span>'
                        
                        # Determine if program is saved for styling
                        saved_class = "saved" if is_saved else ""
                        
                        # Check if this SPECIFIC program (including day/time) is already in any saved schedule
                        in_schedule = None
                        for schedule_name, schedule_programs in st.session_state.saved_schedules.items():
                            if any(prog.get('Program Name') == program_name and 
                                  prog.get('Provider Name') == provider_name and
                                  prog.get('Day of the week') == program.get('Day of the week', '') and
                                  prog.get('Start time') == program.get('Start time', '')
                                  for prog in schedule_programs):
                                in_schedule = schedule_name
                                break
                        
                        # Clickable program card with hover effects
                        card_container = st.container()
                        with card_container:
                            # Add CSS class for styling and selection indicator
                            selected_class = "program-selected" if in_schedule else ""
                            st.markdown(f'<div class="program-card {saved_class} {selected_class}">', unsafe_allow_html=True)
                            
                            # Use full width for program info - no heart button
                            # Optimize text for single line display - more space for program name
                            display_name = program_name[:25] + "..." if len(program_name) > 25 else program_name
                            
                            # Simple tooltip with schedule info if applicable
                            if in_schedule:
                                tooltip_text = f"Provider: {provider_name}. In schedule: {in_schedule}. Click to view full details."
                            else:
                                tooltip_text = f"Provider: {provider_name}. Click to view full details."
                            
                            # Enhanced button with visual badges and child labels for Family View
                            button_key = f"prog_{day}_{time_slot}_{i}"
                            
                            # Add child label for Family View
                            child_label = ""
                            if st.session_state.current_schedule == "Family View" and 'Schedule_Name' in program:
                                schedule_name = program.get('Schedule_Name', '')
                                if schedule_name:
                                    child_label = f"👧 {schedule_name}: "
                            
                            button_text = f"{child_label}{icon} {display_name}" + (" 💖" if in_schedule else "")
                            
                            if st.button(button_text, 
                                       key=button_key,
                                       help=tooltip_text,
                                       use_container_width=True):
                                # Convert pandas Series to dictionary to avoid boolean ambiguity
                                st.session_state.details_program_data = program.to_dict() if hasattr(program, 'to_dict') else program
                                st.session_state.show_program_details = True
                                st.rerun()
                            
                            # Display badges below button if any exist
                            if badges_html:
                                st.markdown(badges_html, unsafe_allow_html=True)
                else:
                    st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
        
        st.markdown("---")

# Initialize session state
if 'selected_days' not in st.session_state:
    st.session_state.selected_days = []
if 'selected_interests' not in st.session_state:
    st.session_state.selected_interests = []
# Removed alternative grid options - keeping standard view only
if 'child_age' not in st.session_state:
    st.session_state.child_age = 5
if 'start_time' not in st.session_state:
    st.session_state.start_time = "03:00 PM"
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
# Removed view_mode - only showing schedule view now
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
if 'show_program_details' not in st.session_state:
    st.session_state.show_program_details = False
if 'show_save_dialog' not in st.session_state:
    st.session_state.show_save_dialog = False
if 'last_schedule_name' not in st.session_state:
    st.session_state.last_schedule_name = ""
if 'save_success_message' not in st.session_state:
    st.session_state.save_success_message = ""

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
        margin-bottom: 0.3rem;
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
    
    /* Compact program card styling with no margins/padding for max text space */
    .program-card .stButton button {
        min-height: 28px !important;
        height: 28px !important;
        max-height: 28px !important;
        padding: 0px !important;
        margin: 0px !important;
        font-size: 0.6rem !important;
        line-height: 1.0 !important;
        text-align: left !important;
        white-space: pre-wrap !important;
        overflow: hidden !important;
        display: block !important;
        background: rgba(255, 255, 255, 0.95) !important;
        color: #262730 !important;
        border: 1px solid rgba(0, 0, 0, 0.1) !important;
        font-weight: normal !important;
        word-break: break-word !important;
        box-sizing: border-box !important;
    }
    
    /* Make program card buttons more compact with no margins/padding for max text space */
    div[data-testid="column"] .stButton button {
        min-height: 28px !important;
        height: 28px !important;
        max-height: 28px !important;
        padding: 0px !important;
        margin: 0px !important;
        font-size: 0.6rem !important;
        line-height: 1.0 !important;
        text-align: left !important;
        white-space: pre-wrap !important;
        overflow: hidden !important;
        display: block !important;
        font-weight: normal !important;
        word-break: break-word !important;
        box-sizing: border-box !important;
    }
    
    /* Remove ALL margins and padding everywhere */
    .program-card .stButton {
        margin: 0px !important;
        padding: 0px !important;
    }
    
    .program-card .stButton > div {
        margin: 0px !important;
        padding: 0px !important;
    }
    
    /* NUCLEAR OPTION - Remove ALL margins and padding everywhere */
    .program-card .stButton,
    .program-card .stButton > div,
    .program-card .stButton button,
    div[data-testid="column"] .stButton,
    div[data-testid="column"] .stButton > div,
    div[data-testid="column"] .stButton button,
    div[data-testid="column"] button,
    .program-card div[data-testid="column"],
    div[data-testid="column"] {
        margin: 0 !important;
        padding: 0 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        align-items: flex-start !important;
        border-spacing: 0 !important;
    }
    
    /* DEBUG: Force 2-line button layout with different approach */
    .program-card .stButton button,
    div[data-testid="column"] .stButton button {
        height: 28px !important;
        min-height: 28px !important;
        max-height: 28px !important;
        font-size: 0.45rem !important;
        line-height: 1.0 !important;
        overflow: hidden !important;
        white-space: pre-line !important;
        word-wrap: break-word !important;
        border: 1px solid #ddd !important;
        background: white !important;
        width: 100% !important;
        box-sizing: border-box !important;
        padding: 2px !important;
        margin: 0 !important;
        display: block !important;
        text-align: left !important;
    }
    
    /* Reduce vertical spacing in schedule grid */
    .program-card {
        margin: 1px 0 !important;
        padding: 1px !important;
    }
    
    .program-card .stButton {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Make time slot containers more compact */
    div[data-testid="column"] {
        padding: 2px !important;
        margin: 0 !important;
    }
    
    /* Reduce spacing in containers */
    .stContainer > div {
        margin: 0 !important;
        padding: 1px 0 !important;
    }
    
    /* Compact the schedule table headers */
    .schedule-view-header {
        margin: 2px 0 !important;
        padding: 4px 0 !important;
    }
    
    /* Reduce spacing around time slot rows */
    .stContainer {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* AGGRESSIVE spacing reduction */
    .stMarkdown {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    div[data-testid="stVerticalBlock"] > div {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Target all containers more aggressively */
    .main .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.5rem !important;
    }
    
    /* Remove gaps around every element */
    .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* ELIMINATE ALL VERTICAL SPACING */
    div {
        margin: 0 !important;
    }
    
    /* Target Streamlit containers specifically */
    .stButton {
        margin: 0 !important;
        padding: 0 !important;
        margin-bottom: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Remove spacing around program cards */
    .program-card {
        margin: 0 !important;
        padding: 0 !important;
        margin-bottom: 1px !important;
    }
    
    /* Make containers ultra compact */
    [data-testid="column"] {
        padding: 0 !important;
        margin: 0 !important;
        gap: 0 !important;
    }
    
    /* Hide the dot buttons with multiple approaches */
    .program-card .stButton,
    .program-card .stButton > div,
    .program-card .stButton button {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        width: 0px !important;
        opacity: 0 !important;
        position: absolute !important;
        top: -9999px !important;
        left: -9999px !important;
        z-index: -999 !important;
        pointer-events: none !important;
    }
    
    /* Target any button that's small and contains a dot */
    button {
        font-size: inherit !important;
    }
    
    button[style*="display: none"] {
        display: none !important;
    }
    
    /* Clean program button styling - more compact for tighter rows */
    .stButton button {
        font-size: 0.65rem !important;
        padding: 3px 6px !important;
        min-height: 28px !important;
        height: 28px !important;
        text-align: left !important;
        justify-content: flex-start !important;
        font-weight: 500 !important;
        border-radius: 4px !important;
        border: 1px solid #e1e5e9 !important;
        background: #ffffff !important;
        color: #262730 !important;
        overflow: hidden !important;
        white-space: nowrap !important;
        text-overflow: ellipsis !important;
    }
    
    /* Visual indicator for programs already in schedules */
    .stButton.program-selected button {
        border-left: 3px solid #28a745 !important;
        background: rgba(40, 167, 69, 0.05) !important;
    }
    
    /* Hover states */
    .stButton button:hover {
        border-color: #1E3D59 !important;
        background: #f8f9fa !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(30, 61, 89, 0.1) !important;
    }
    
    .stButton.program-selected button:hover {
        background: rgba(40, 167, 69, 0.1) !important;
    }
    
    /* Much more compact button container spacing */
    .stButton {
        margin: 1px 0 !important;
    }
    
    /* Reduce vertical spacing in schedule grid containers */
    div[data-testid="column"] {
        padding: 1px 2px !important;
    }
    
    /* Clean primary and secondary button styling */
    button[data-testid="stButton-primary"] {
        background: #1E3D59 !important;
        color: white !important;
        border: 1px solid #1E3D59 !important;
        font-weight: 600 !important;
    }
    
    button[data-testid="stButton-secondary"] {
        background: #f8f9fa !important;
        color: #1E3D59 !important;
        border: 1px solid #e1e5e9 !important;
        font-weight: 400 !important;
    }
    
    /* Nuclear option - hide ALL tiny buttons that might be dots */
    button[style*="height: 0"] {
        display: none !important;
    }
    
    /* Hide buttons with minimal text content */
    button[data-baseweb="button"]:not([title]):not([aria-label]) {
        font-size: inherit !important;
    }
    
    /* More aggressive - hide any button that's very small */
    button[data-testid^="baseButton"]:not([title]):not([aria-label]) {
        font-size: inherit !important;
    }
    
    /* Target buttons that appear to be single character */
    .stButton button:not([title]):not([aria-label]) {
        font-size: inherit !important;
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
    // Simple tooltip enhancement for better mobile experience
    document.addEventListener('DOMContentLoaded', function() {
        // Add better tooltip behavior if needed
        console.log('Schedule grid loaded with enhanced tooltips');
    });
    
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
    
    # Create time options - 30-minute intervals from 8:00 AM to 8:00 PM
    time_options = []
    
    # Add AM times: 8:00 AM to 11:30 AM
    for hour in range(8, 12):
        time_options.append(f"{hour:02d}:00 AM")
        time_options.append(f"{hour:02d}:30 AM")
    
    # Add 12:00 PM and 12:30 PM
    time_options.append("12:00 PM")
    time_options.append("12:30 PM")
    
    # Add PM times: 1:00 PM to 8:00 PM
    for hour in range(1, 9):
        time_options.append(f"{hour:02d}:00 PM")
        if hour < 8:  # Don't add 8:30 PM since we stop at 8:00 PM
            time_options.append(f"{hour:02d}:30 PM")

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
        
        # Submit button with mobile-optimized styling
        st.markdown('<div class="submit-section primary-action">', unsafe_allow_html=True)
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
            
            # Create mobile-friendly progress indicator
            progress_container = st.empty()
            
            # Step 1: Searching for programs
            progress_container.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 15px 20px;
                border-radius: 12px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            ">
                <div style="
                    color: white;
                    font-size: 1.1rem;
                    font-weight: 600;
                    margin-bottom: 8px;
                ">
                    🔍 Searching for programs...
                </div>
                <div style="
                    color: rgba(255,255,255,0.8);
                    font-size: 0.9rem;
                ">
                    Finding programs that match your criteria
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Small delay to show the first step
            time.sleep(0.5)
            
            # Step 2: Fetching program details
            progress_container.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 15px 20px;
                border-radius: 12px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            ">
                <div style="
                    color: white;
                    font-size: 1.1rem;
                    font-weight: 600;
                    margin-bottom: 8px;
                ">
                    📋 Fetching program details...
                </div>
                <div style="
                    color: rgba(255,255,255,0.8);
                    font-size: 0.9rem;
                ">
                    Loading schedules and locations
                </div>
            </div>
            """, unsafe_allow_html=True)
            
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
            
            # Step 3: Loading schedules
            progress_container.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 15px 20px;
                border-radius: 12px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            ">
                <div style="
                    color: white;
                    font-size: 1.1rem;
                    font-weight: 600;
                    margin-bottom: 8px;
                ">
                    📅 Loading schedules...
                </div>
                <div style="
                    color: rgba(255,255,255,0.8);
                    font-size: 0.9rem;
                ">
                    Preparing your personalized results
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(0.3)
            
            # Final step: Show results
            program_count = len(filtered_df)
            if program_count == 0:
                final_message = "😔 No programs found matching your criteria"
                final_subtitle = "Try adjusting your search filters"
                final_color = "linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%)"
            elif program_count == 1:
                final_message = "🎉 Found 1 perfect program!"
                final_subtitle = "Great match for your child"
                final_color = "linear-gradient(135deg, #2ecc71 0%, #27ae60 100%)"
            else:
                final_message = f"🎉 Found {program_count} programs!"
                final_subtitle = "Multiple options available for your child"
                final_color = "linear-gradient(135deg, #2ecc71 0%, #27ae60 100%)"
            
            progress_container.markdown(f"""
            <div style="
                background: {final_color};
                padding: 15px 20px;
                border-radius: 12px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                animation: pulse 2s infinite;
            ">
                <div style="
                    color: white;
                    font-size: 1.2rem;
                    font-weight: 700;
                    margin-bottom: 8px;
                ">
                    {final_message}
                </div>
                <div style="
                    color: rgba(255,255,255,0.9);
                    font-size: 0.9rem;
                ">
                    {final_subtitle}
                </div>
            </div>
            <style>
            @keyframes pulse {{
                0% {{ transform: scale(1); }}
                50% {{ transform: scale(1.02); }}
                100% {{ transform: scale(1); }}
            }}
            </style>
            """, unsafe_allow_html=True)
            
            time.sleep(1)
            progress_container.empty()  # Clear the progress indicator
            
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
            margin: 0.3rem 0 0.2rem 0 !important;
            text-align: center !important;
            padding: 0.5rem !important;
            font-weight: 600 !important;
        }}
        </style>
        <div class="result-count-text">{result_text}</div>
        """, unsafe_allow_html=True)
        
        # Mobile-Optimized Navigation Bar  
        if len(filtered_df) > 0:
            # Initialize map visibility state
            if 'show_map' not in st.session_state:
                st.session_state.show_map = False
            
            # Use Streamlit container with CSS styling (more reliable approach)
            with st.container():
                st.markdown("""
                <style>
                /* Simple, working navigation bar */
                .stContainer {
                    background: white !important;
                    padding: 15px !important;
                    border: 1px solid #e9ecef !important;
                    border-radius: 8px !important;
                    margin-bottom: 20px !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Schedule selection - label and dropdown on same line
                nav_col1, nav_col2 = st.columns([1, 3])
                
                with nav_col1:
                    st.markdown("**📅 View Schedule for:**")
                
                with nav_col2:
                    # Create schedule options with program counts
                    schedule_options = ["All Programs"]
                    schedule_name_mapping = {"All Programs": "All Programs"}
                    
                    # Add saved schedules with program counts
                    total_family_programs = 0
                    for schedule_name, programs in st.session_state.saved_schedules.items():
                        program_count = len(programs)
                        total_family_programs += program_count
                        if program_count == 1:
                            display_name = f"{schedule_name} (1 program)"
                        else:
                            display_name = f"{schedule_name} ({program_count} programs)"
                        schedule_options.append(display_name)
                        schedule_name_mapping[display_name] = schedule_name
                    
                    # Add Family View if there are multiple schedules
                    if len(st.session_state.saved_schedules) > 1 and total_family_programs > 0:
                        family_display_name = f"Family View ({total_family_programs} total)"
                        schedule_options.append(family_display_name)
                        schedule_name_mapping[family_display_name] = "Family View"
                    
                    # Find current schedule display name for index
                    current_display_name = "All Programs"
                    if st.session_state.current_schedule != "All Programs":
                        for display_name, actual_name in schedule_name_mapping.items():
                            if actual_name == st.session_state.current_schedule:
                                current_display_name = display_name
                                break
                    
                    try:
                        current_index = schedule_options.index(current_display_name)
                    except ValueError:
                        current_index = 0  # Default to "All Programs"
                    
                    # Create dropdown for schedule selection
                    selected_display = st.selectbox(
                        "",
                        options=schedule_options,
                        index=current_index,
                        key="schedule_dropdown",
                        label_visibility="collapsed",
                        help="Select which schedule to display"
                    )
                    
                    # Convert display name back to actual schedule name
                    selected_schedule = schedule_name_mapping[selected_display]
                    
                    # Update current schedule if changed with loading indicator
                    if selected_schedule != st.session_state.current_schedule:
                        # Show loading indicator
                        loading_container = st.empty()
                        loading_container.markdown("""
                        <div style="
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                            padding: 12px 20px;
                            border-radius: 8px;
                            text-align: center;
                            margin: 10px 0;
                            color: white;
                            font-weight: 500;
                        ">
                            🔄 Switching to {selected_display}...
                        </div>
                        """.format(selected_display=selected_display), unsafe_allow_html=True)
                        
                        st.session_state.current_schedule = selected_schedule
                        st.rerun()
                
                # Map toggle button
                st.markdown("**🗺️ Map:**")
                map_button_text = "Hide Map" if st.session_state.show_map else "Show Map"
                if st.button(map_button_text, key="map_toggle"):
                    st.session_state.show_map = not st.session_state.show_map
                    st.rerun()
            
            # Show Family View summary or individual schedule conflicts
            current_schedule_display = st.session_state.current_schedule
            
            if current_schedule_display == "Family View":
                # Family View Summary
                st.markdown("---")
                
                # Calculate family statistics
                total_programs = sum(len(programs) for programs in st.session_state.saved_schedules.values())
                schedule_count = len(st.session_state.saved_schedules)
                
                # Calculate total weekly cost using Cost Per Class field only
                total_cost = 0
                cost_count = 0
                for schedule_name, programs in st.session_state.saved_schedules.items():
                    for prog in programs:
                        # Only use Cost Per Class (this is the actual per-class cost)
                        if 'Cost Per Class' in prog and prog['Cost Per Class'] and not pd.isna(prog['Cost Per Class']):
                            try:
                                cost_per_class = float(prog['Cost Per Class'])
                                if cost_per_class > 0:
                                    total_cost += cost_per_class
                                    cost_count += 1
                            except (ValueError, TypeError):
                                pass
                
                # Display family summary
                summary_text = f"👨‍👩‍👧‍👦 **Family Schedule:** {total_programs} programs across {schedule_count} schedules"
                if total_cost > 0:
                    summary_text += f" • **Total weekly cost:** ${total_cost:.2f}"
                
                st.markdown(f"""
                <div style="background: #e8f5e8; border: 1px solid #4caf50; border-radius: 8px; padding: 12px; margin-bottom: 15px;">
                    <div style="color: #2e7d32; font-weight: 600;">{summary_text}</div>
                </div>
                """, unsafe_allow_html=True)
                
            elif current_schedule_display != "All Programs":
                # Individual schedule conflicts
                conflicts = detect_schedule_conflicts(current_schedule_display)
                if conflicts:
                    st.markdown("---")
                    conflict_text = f"⚠️ {len(conflicts)} scheduling conflicts detected in {current_schedule_display}"
                    st.warning(conflict_text)
                    
                    for conflict in conflicts:
                        st.error(f"**{conflict['day']}**: {conflict['program1']} ({conflict['time1']}) overlaps with {conflict['program2']} ({conflict['time2']})")
            
            # Filter programs by current schedule
            display_df = filter_programs_by_schedule(filtered_df, st.session_state.current_schedule)
            
            # Update filtered_df for display
            filtered_df = display_df
        
        # Collapsible Map Section - Only show if toggle is enabled
        if len(filtered_df) > 0 and st.session_state.show_map:
            # Get coordinates for all programs
            program_coords = []
            for _, program in filtered_df.iterrows():
                prog_coords = geocode_address(program['Address'])
                if prog_coords:
                    program_coords.append((prog_coords, program))
            
            if program_coords:
                # Map container with mobile-optimized styling
                st.markdown("""
                <style>
                .map-container {
                    background: #f8f9fa;
                    border-radius: 12px;
                    padding: 15px;
                    margin: 15px 0;
                    border: 1px solid #e9ecef;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }
                .map-header {
                    font-size: 1.1rem !important;
                    font-weight: 600 !important;
                    color: #1E3D59 !important;
                    margin: 0 0 15px 0 !important;
                    padding: 0 !important;
                    text-align: center;
                }
                @media (max-width: 768px) {
                    .map-container {
                        margin: 10px -1rem;
                        border-radius: 0;
                        border-left: none;
                        border-right: none;
                        padding: 15px 1rem;
                    }
                    .map-header {
                        font-size: 1rem !important;
                    }
                }
                </style>
                <div class="map-container">
                    <div class="map-header">🗺️ Program Locations</div>
                """, unsafe_allow_html=True)
                
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
                
                # Responsive map sizing - optimized height for mobile
                map_height = 350  # Reduced height for mobile optimization
                st_folium(m, width="100%", height=map_height, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Display results in schedule view format with enhanced empty states
        if len(filtered_df) > 0:
            # Schedule View - only view mode available
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
                    margin: 0.1rem 0 0.3rem 0 !important;
                    font-style: italic !important;
                }
                </style>
                <div class="schedule-view-header">📅 Weekly Schedule</div>
                <div class="schedule-instruction">Click ♡ to save programs to your schedule</div>
                """, unsafe_allow_html=True)
            # Use standard grid with improved vertical spacing
            display_schedule_grid(filtered_df)
        else:
            # Enhanced empty states based on current view
            current_schedule = st.session_state.current_schedule
            
            if current_schedule == "All Programs":
                st.info("💡 **No programs found matching your criteria.**\n\n**Try adjusting your filters:**\n- Increase the distance range\n- Select fewer interest categories\n- Adjust the time range\n- Check more days of the week")
            elif current_schedule == "Family View":
                if not st.session_state.saved_schedules:
                    st.info("👨‍👩‍👧‍👦 **Family View is empty.**\n\nCreate some individual schedules first, then come back to see the combined family view!")
                else:
                    st.info("👨‍👩‍👧‍👦 **No programs in any schedules yet.**\n\nSave some programs to your individual schedules to see them here!")
            else:
                # Individual schedule empty state
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 30px 20px;
                    border-radius: 16px;
                    text-align: center;
                    border: 2px dashed #dee2e6;
                    margin: 20px 0;
                ">
                    <div style="font-size: 3rem; margin-bottom: 15px;">📅</div>
                    <div style="font-size: 1.2rem; font-weight: 600; color: #495057; margin-bottom: 10px;">
                        No programs in "{current_schedule}" yet
                    </div>
                    <div style="color: #6c757d; font-size: 0.95rem; line-height: 1.5;">
                        Search for programs above and click the ♡ button to save them to this schedule!
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Modal dialogs are triggered by session state flags
        if st.session_state.get('show_program_details') and st.session_state.get('details_program_data'):
            program_details_modal()
        
        # Show save dialog when triggered from program details
        if st.session_state.get('show_save_dialog') and st.session_state.get('popup_program_data'):
            save_program_dialog()
    
except Exception as e:
    st.error(f"Error: {str(e)}")
