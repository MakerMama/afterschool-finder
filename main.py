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

# Clean, Professional Button System
st.markdown("""
<style>
/* Professional Button System - Mobile First */

/* PRIMARY BUTTONS - Main actions */
.primary-action button {
    min-height: 48px !important;
    padding: 14px 24px !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    background: #1E3D59 !important;
    border: none !important;
    color: white !important;
    font-size: 1rem !important;
    transition: all 0.2s ease !important;
}

.primary-action button:hover {
    background: #2a4a66 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(30, 61, 89, 0.3) !important;
}

/* SECONDARY BUTTONS - Supporting actions */
.secondary-action button {
    min-height: 44px !important;
    padding: 10px 20px !important;
    border-radius: 6px !important;
    background: white !important;
    border: 2px solid #1E3D59 !important;
    color: #1E3D59 !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease !important;
}

.secondary-action button:hover {
    background: #f8f9fa !important;
    transform: translateY(-1px) !important;
}

/* MODAL ACTIONS - Dialog buttons */
.modal-actions {
    margin-top: 20px !important;
    display: flex !important;
    gap: 12px !important;
    justify-content: center !important;
}

.modal-actions button {
    min-height: 44px !important;
    min-width: 120px !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
}

/* MOBILE RESPONSIVE */
@media (max-width: 768px) {
    .primary-action button {
        min-height: 52px !important;
        padding: 16px 24px !important;
        font-size: 1.05rem !important;
    }
    
    .modal-actions {
        flex-direction: column !important;
        gap: 8px !important;
    }
    
    .modal-actions button {
        width: 100% !important;
        min-height: 48px !important;
    }
}

/* TOUCH OPTIMIZATION */
button {
    touch-action: manipulation !important;
    -webkit-tap-highlight-color: rgba(0,0,0,0.1) !important;
}
</style>
""", unsafe_allow_html=True)

# Helper functions for display
def display_program_card(program):
    """Display a program as a card in list view"""
    with st.container():
        # Determine program type badge and border color
        program_type = program.get('Program Type', '')
        if program_type == 'On-site':
            border_color = '#A7E1E5'  # Pastel teal for on-site
            type_badge = '<span style="background: #A7E1E5; color: #2C3E50; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-right: 6px;">On-site</span>'
        elif program_type == 'Off-site':
            border_color = '#FFD4A3'  # Pastel peach for off-site
            type_badge = '<span style="background: #FFD4A3; color: #2C3E50; padding: 3px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; margin-right: 6px;">Off-site</span>'
        else:
            border_color = '#E2E8F0'  # Default gray
            type_badge = ''

        html = f"""
        <div class='program-card-container' style='border-left: 4px solid {border_color};'>
            <h3 class='program-card-title'>{program.get('Program Name', 'N/A')}</h3>
            <p class='program-card-provider'>{program.get('Provider Name', 'N/A')}</p>
            <div style='margin: 8px 0;'>
                {type_badge}
            </div>
            <div class='program-card-info-bar'>
                <p class='program-card-text'><span style='margin-right: 8px;'>⏰</span>{program.get('Day of the week', 'N/A')} • {program.get('Start time', 'N/A')} - {program.get('End time', 'N/A')}</p>"""
        
        # Add cost and distance to key info bar
        if 'Distance' in program and not pd.isna(program['Distance']):
            html += f"<p class='program-card-text'><span style='margin-right: 8px;'>📍</span>{program['Distance']:.2f} miles away</p>"
        
        cost_info = []
        enrollment_type = program.get('Enrollment Type', '').strip() if isinstance(program.get('Enrollment Type'), str) else ''
        
        if 'Cost' in program and not pd.isna(program['Cost']):
            base_cost = f"${program['Cost']:,.2f}"
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
            cost_info.append(f"${program['Cost Per Class']:,.2f}/class")
        
        if cost_info:
            html += f"<p class='program-card-text'><span style='margin-right: 8px;'>💰</span>{' • '.join(cost_info)}</p>"
        html += "</div>"
        
        # Secondary details
        min_age_val = program.get('Min Age', 0)
        max_age_val = program.get('Max Age', 0)
        min_age_safe = int(float(min_age_val)) if min_age_val is not None and not pd.isna(min_age_val) else 0
        max_age_safe = int(float(max_age_val)) if max_age_val is not None and not pd.isna(max_age_val) else 0
        html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>👶</span><strong>Ages:</strong> {min_age_safe} - {max_age_safe}</p>"

        # Show Program Type badge
        program_type = program.get('Program Type', '')
        if program_type and not pd.isna(program_type):
            type_color = '#A7E1E5' if program_type == 'On-site' else '#FFD4A3'
            html += f"<p class='program-card-secondary'><span style='background: {type_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; margin-right: 6px;'>{program_type}</span>"

            # Show Grade Level for on-site programs
            if program_type == 'On-site':
                grade_level = program.get('Grade_Level', '')
                if grade_level and not pd.isna(grade_level) and str(grade_level).strip():
                    html += f"<strong>Grades:</strong> {grade_level}"
            html += "</p>"

        html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>🎯</span><strong>Category:</strong> {program.get('Interest Category', 'N/A')}</p>"
        html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>📍</span><strong>Address:</strong> {program.get('Address', 'N/A')}</p>"

        # Contact & additional info
        if 'Website' in program and not pd.isna(program['Website']):
            html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>🌐</span><a href='{program['Website']}' target='_blank' class='program-card-link'>Website</a></p>"
        if 'Contact Phone' in program and not pd.isna(program['Contact Phone']):
            html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>📞</span><strong>Phone:</strong> {program['Contact Phone']}</p>"
        if 'School Pickup From' in program and isinstance(program['School Pickup From'], str) and program['School Pickup From'].strip():
            html += f"<p class='program-card-secondary'><span style='margin-right: 6px;'>🚌</span><strong>School Pickup:</strong> {program['School Pickup From']}</p>"
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
        'Program Type': program.get('Program Type', ''),
        'Grade_Level': program.get('Grade_Level', ''),
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

        st.markdown(f"### {icon} {program.get('Program Name', 'N/A')}")
        st.markdown(f"{program.get('Provider Name', 'N/A')}")
        
        # Show distance badge only (availability status removed as it's now on cards)
        if distance_text:
            # Use warm terra cotta styling for distance badges - friendly and distinct
            distance_badge = f'<span style="font-size: 0.8rem; background: var(--distance-color); color: #2C3E50; padding: 5px 12px; border-radius: 20px; margin-right: 6px; font-weight: 500; box-shadow: 0 2px 4px rgba(221, 107, 32, 0.3);">🏠 {distance_text}</span>'
            st.markdown(distance_badge, unsafe_allow_html=True)
    
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
                st.session_state.save_success_message = ""  # Clear previous success message
                # Clear save context for regular saves (not from Add Programs)
                st.session_state.save_context_schedule = None
                st.session_state.show_save_dialog = True
                st.session_state.show_program_details = False  # Close details modal
                st.rerun()

    # Program description (if available)
    description = program.get('Description')
    if description is not None and not pd.isna(description) and str(description).strip():
        st.markdown("---")
        st.markdown("**📝 Program Description**")
        st.markdown(f"{description}")

    st.markdown("---")

    # Program details in two columns
    detail_col1, detail_col2 = st.columns([3, 2])
    
    with detail_col1:
        st.markdown("#### 📅 Schedule Information")
        st.text(f"Day: {program.get('Day of the week', 'N/A')}")
        st.text(f"Time: {program.get('Start time', 'N/A')} - {program.get('End time', 'N/A')}")

        # Format and display program dates
        start_date = program.get('Start date')
        end_date = program.get('End date')
        if start_date and end_date and not pd.isna(start_date) and not pd.isna(end_date):
            try:
                # Parse the dates (assuming format like "9/8/2025")
                start_dt = pd.to_datetime(start_date)
                end_dt = pd.to_datetime(end_date)
                # Format nicely: "September 8, 2025 - December 16, 2025"
                formatted_dates = f"{start_dt.strftime('%B %d, %Y')} - {end_dt.strftime('%B %d, %Y')}"
                st.text(f"Dates: {formatted_dates}")
            except:
                # Fallback to raw values if parsing fails
                st.text(f"Dates: {start_date} - {end_date}")

        # Show Program Type
        program_type = program.get('Program Type', '')
        if program_type and not pd.isna(program_type):
            st.text(f"Type: {program_type}")

            # Show Grade Level for on-site programs
            if program_type == 'On-site':
                grade_level = program.get('Grade_Level', '')
                if grade_level and not pd.isna(grade_level) and str(grade_level).strip():
                    st.text(f"Grade Levels: {grade_level}")

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

            # Show note if program has fractional age requirements
            has_fractional = False
            if min_age_val is not None and not pd.isna(min_age_val):
                if float(min_age_val) % 1 != 0:  # Has decimal component
                    has_fractional = True
            if max_age_val is not None and not pd.isna(max_age_val):
                if float(max_age_val) % 1 != 0:  # Has decimal component
                    has_fractional = True

            if has_fractional:
                st.info(f"ℹ️ This program has specific age requirements (min age: {min_age_val}). Please contact the provider to verify your child's eligibility.")

        st.text(f"Category: {program.get('Interest Category', 'N/A')}")
        
        # Add prerequisite information if available
        prerequisite = program.get('Prerequisite')
        if prerequisite is not None and not pd.isna(prerequisite) and str(prerequisite).strip() and str(prerequisite).lower() not in ['none', 'n/a', '']:
            st.text(f"Prerequisites: {prerequisite}")
        
        st.markdown("#### 💰 Pricing")
        cost_info = []
        cost = program.get('Cost')
        if cost is not None and not pd.isna(cost):
            enrollment_type = program.get('Enrollment Type', '')
            enrollment_type = enrollment_type.strip() if isinstance(enrollment_type, str) else ''
            base_cost = f"${float(cost):,.2f}"
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
            cost_info.append(f"${float(cost_per_class):,.2f}/class")
        
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
            st.markdown("#### 🚌 School Pickup")
            st.text(f"{school_pickup}")
    
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
        background: linear-gradient(135deg, var(--availability-color) 0%, #48BB78 100%) !important;
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
    
    # Single column layout - focused on schedule selection
    st.markdown("### Select Schedule")
    
    # Show context indicator if we're adding to a specific schedule
    if st.session_state.save_context_schedule:
        st.info(f"🎯 Adding program to **{st.session_state.save_context_schedule}'s schedule**")
    
    # Schedule selection
    existing_schedules = list(st.session_state.saved_schedules.keys())
    schedule_options = ["-- Create New Schedule --"] + existing_schedules
    
    # Determine default selection based on context
    default_index = 0  # Default to "Create New Schedule"
    selectbox_key = "modal_schedule_selectbox"
    
    # If we have a save context (from Add Programs button), pre-select that schedule
    if st.session_state.save_context_schedule and st.session_state.save_context_schedule in existing_schedules:
        context_schedule = st.session_state.save_context_schedule
        default_index = existing_schedules.index(context_schedule) + 1  # +1 because of "Create New" option
        
        # Clear the existing selectbox state to force re-evaluation
        if selectbox_key in st.session_state:
            del st.session_state[selectbox_key]
    
    selected_option = st.selectbox(
        "Choose a schedule:",
        options=schedule_options,
        index=default_index,
        key=selectbox_key
    )
    
    # Schedule name input with dynamic contextual help and smart defaults
    if selected_option == "-- Create New Schedule --":
        schedule_name = st.text_input(
            "Schedule Name:",
            value="",
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
            
            # Only show validation messages for new schedules, not existing ones
            elif schedule_name not in st.session_state.saved_schedules:
                # Check for good naming (looks like a name)
                if (len(schedule_name) >= 2 and 
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
    
    # Show success message if available
    if st.session_state.save_success_message:
        st.markdown(f'<div class="save-success">✅ {st.session_state.save_success_message}</div>', unsafe_allow_html=True)
        # Clear success message after showing it
        st.session_state.save_success_message = ""
    
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
                    
                    # Clear popup state and close modal
                    st.session_state.show_save_popup = False
                    st.session_state.show_save_dialog = False
                    st.session_state.popup_program_data = None
                    # Clear the save context since we've successfully saved
                    st.session_state.save_context_schedule = None

                    # Rerun to close dialog (will scroll to top, but that's the trade-off)
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
            # Clear the save context when canceling
            st.session_state.save_context_schedule = None
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

def get_desktop_encouragement_hint(filtered_df, current_schedule):
    """Generate smart hints to encourage desktop grid view when beneficial."""
    if current_schedule == 'All Programs':
        return None
    
    # Count programs across multiple days
    days_with_programs = len(filtered_df['Day of the week'].unique()) if len(filtered_df) > 0 else 0
    total_programs = len(filtered_df)
    
    if days_with_programs >= 3 and total_programs >= 3:
        return "💡 **Grid view** shows all your programs at once - perfect for spotting time conflicts and scheduling gaps!"
    elif total_programs >= 5:
        return "💡 **Grid view** helps visualize your busy schedule across the full week"
    elif days_with_programs >= 2:
        return "💡 See all your program days side-by-side in **Grid view**"
    
    return None

def display_mobile_schedule_view(filtered_df):
    """Display mobile-optimized single day view with program cards."""

    # Define correct day order
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # Sort days in correct week order instead of alphabetically
    if len(filtered_df) > 0:
        unique_days = filtered_df['Day of the week'].unique()
        available_days = [day for day in day_order if day in unique_days]
    else:
        available_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    
    # Initialize selected day in session state
    if 'mobile_selected_day' not in st.session_state:
        st.session_state.mobile_selected_day = available_days[0] if available_days else 'Monday'
    
    # Streamlined day selection with tabs-style interface
    st.markdown('<div style="margin: 10px 0;">', unsafe_allow_html=True)
    
    # Create horizontal day selector buttons
    cols = st.columns(len(available_days))
    for i, day in enumerate(available_days):
        with cols[i]:
            day_short = day[:3]  # Mon, Tue, Wed, etc.
            is_selected = day == st.session_state.mobile_selected_day
            button_style = "primary" if is_selected else "secondary"
            
            if st.button(day_short, key=f"day_tab_{day}", type=button_style, use_container_width=True):
                st.session_state.mobile_selected_day = day
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

    selected_day = st.session_state.mobile_selected_day
    
    # Filter programs for selected day
    day_programs = filtered_df[filtered_df['Day of the week'] == selected_day].copy()
    
    if len(day_programs) == 0:
        st.info(f"📅 No programs found for {selected_day}.\n\nTry selecting a different day or adjusting your filters.")
        return
    
    # Sort programs by start time
    day_programs['start_time_minutes'] = day_programs['Start time'].apply(
        lambda x: parse_time(x) if pd.notna(x) and str(x).strip() else 0
    )
    day_programs = day_programs.sort_values('start_time_minutes')
    
    # Get current schedule name for combined header
    current_schedule = st.session_state.get('current_schedule', 'Schedule')
    if current_schedule == 'All Programs':
        header_text = f"📅 {selected_day} Programs ({len(day_programs)} found)"
    else:
        header_text = f"📅 {current_schedule}'s {selected_day} Schedule ({len(day_programs)} found)"
    
    st.markdown(f'<div style="font-size: var(--font-size-large); font-weight: 600; color: var(--primary-color); margin: 1rem 0; text-align: center;">{header_text}</div>', unsafe_allow_html=True)
    
    # Show smart desktop encouragement hint
    current_schedule = st.session_state.get('current_schedule', 'Schedule')
    hint = get_desktop_encouragement_hint(filtered_df, current_schedule)
    if hint:
        st.info(hint)
    
    # Display programs as mobile cards
    for idx, (_, program) in enumerate(day_programs.iterrows()):
        with st.container():
            # Create mobile card with all program details
            program_name = program.get('Program Name', 'Program')
            provider_name = program.get('Provider Name', 'Provider')
            start_time = program.get('Start time', 'TBD')
            end_time = program.get('End time', 'TBD')
            address = program.get('Address', 'Address TBD')
            min_age = program.get('Min Age', 'N/A')
            max_age = program.get('Max Age', 'N/A')
            cost = program.get('Cost', 0)
            category = program.get('Interest Category', 'General')
            
            # Get visual elements
            category_icon = get_category_icon(category)
            distance_class, distance_text = get_distance_badge_info(program.get('Distance', 0))

            # Get program type badge text (for mobile display)
            program_type = program.get('Program Type', '')
            if program_type == 'On-site':
                type_badge_text = 'On-site'
            elif program_type == 'Off-site':
                type_badge_text = 'Off-site'
            else:
                type_badge_text = ''

            # Check if program is already saved to any schedule
            program_key = f"{program_name}|{provider_name}|{program.get('Day of the week', '')}|{start_time}"
            is_saved = False
            for schedule_programs in st.session_state.saved_schedules.values():
                for saved_prog in schedule_programs:
                    saved_key = f"{saved_prog.get('Program Name', '')}|{saved_prog.get('Provider Name', '')}|{saved_prog.get('Day of the week', '')}|{saved_prog.get('Start time', '')}"
                    if saved_key == program_key:
                        is_saved = True
                        break
                if is_saved:
                    break
            
            # Show heart icon if saved
            if is_saved:
                heart_badge = '<span style="color: #dc3545; font-weight: 600;">❤️ Saved</span>'
                status_display = heart_badge
            else:
                status_display = ''
            
            # Format cost display
            if cost and cost > 0:
                cost_display = f"${cost:.0f}"
            else:
                cost_display = "Price TBD"
            
            # Format age range
            if pd.notna(min_age) and pd.notna(max_age):
                age_display = f"Ages {int(min_age)}-{int(max_age)}"
            else:
                age_display = "All ages"
            
            # Format the distance text
            distance_display = f' • 🚗 {distance_text}' if distance_text else ''
            
            # Make entire card clickable for details - clean multiline format
            card_content = f"""{category_icon} {program_name}
⏰ {start_time} - {end_time}
📍 {provider_name}"""

            # Add program location badge
            if type_badge_text:
                card_content += f"\n📍 {type_badge_text}"
            
            # Program info and save button on one line
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(card_content, key=f"mobile_card_{idx}", use_container_width=True, help="Tap to view full program details"):
                    st.session_state.details_program_data = program.to_dict() if hasattr(program, 'to_dict') else program
                    st.session_state.show_program_details = True
                    st.rerun()
            with col2:
                if st.button("💾 Save", key=f"mobile_save_{idx}", use_container_width=True):
                    st.session_state.popup_program_data = program.to_dict() if hasattr(program, 'to_dict') else program
                    st.session_state.save_success_message = ""  # Clear previous success message
                    # Clear save context for regular saves (not from Add Programs)
                    st.session_state.save_context_schedule = None
                    st.session_state.show_save_dialog = True
                    st.rerun()
            
            # Add spacing between cards
            st.markdown('<div style="margin-bottom: 10px;"></div>', unsafe_allow_html=True)

def display_schedule_grid(filtered_df):
    """Display programs in a weekly schedule grid with interactive save buttons (ORIGINAL VERSION)"""
    if len(filtered_df) == 0:
        return
        
    # No header needed - keeping it clean
    
    # Add CSS for visual indicators
    st.markdown("""
    <style>
    .schedule-selected {
        border-left: 3px solid var(--availability-color) !important;
        background: rgba(56, 161, 105, 0.08) !important;
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
    
    # Schedule Grid Headers
    st.markdown("""
    <style>
    .schedule-day-header, .schedule-time-header {
        font-weight: 700 !important;
        color: var(--primary-color) !important;
        text-align: center !important;
        padding: 12px 8px !important;
        background: var(--secondary-color) !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-color) !important;
        margin-bottom: 12px !important;
    }
    
    .schedule-day-header { font-size: 1.1rem !important; }
    .schedule-time-header { font-size: 1rem !important; }
    
    @media (max-width: 768px) {
        .schedule-day-header, .schedule-time-header {
            font-size: 0.9rem !important;
            padding: 10px 6px !important;
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

                        # Get program type badge
                        program_type = program.get('Program Type', '')
                        if program_type == 'On-site':
                            type_badge = f'<span style="font-size: 0.7rem; background: #A7E1E5; color: #2C3E50; padding: 4px 10px; border-radius: 12px; margin-right: 4px; font-weight: 500;">On-site</span>'
                        elif program_type == 'Off-site':
                            type_badge = f'<span style="font-size: 0.7rem; background: #FFD4A3; color: #2C3E50; padding: 4px 10px; border-radius: 12px; margin-right: 4px; font-weight: 500;">Off-site</span>'
                        else:
                            type_badge = ''

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
                        
                        # Create visual badges for program type and distance
                        badges_html = ""
                        # Program location badge first
                        if type_badge:
                            badges_html += type_badge
                        # Distance badge last
                        if distance_text:
                            badges_html += f'<span style="font-size: 0.7rem; background: var(--distance-color); color: #2C3E50; padding: 4px 10px; border-radius: 15px; font-weight: 500;">🚶‍♀️ {distance_text}</span>'
                        
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
                            
                            # Truncate provider and program names for two-line display
                            # Provider name uses smaller font (75%), so can fit more characters
                            display_provider = provider_name[:35] + "..." if len(provider_name) > 35 else provider_name
                            display_program = program_name[:20] + "..." if len(program_name) > 20 else program_name

                            # Simple tooltip with full names and schedule info
                            if in_schedule:
                                tooltip_text = f"{provider_name} - {program_name}. In schedule: {in_schedule}. Click to view full details."
                            else:
                                tooltip_text = f"{provider_name} - {program_name}. Click to view full details."

                            # Enhanced button with visual badges and child labels for Family View
                            button_key = f"prog_{day}_{time_slot}_{i}"

                            # Add child label for Family View
                            child_label = ""
                            if st.session_state.current_schedule == "Family View" and 'Schedule_Name' in program:
                                schedule_name = program.get('Schedule_Name', '')
                                if schedule_name:
                                    child_label = f"👧 {schedule_name}: "

                            # Two-line button text: provider (smaller, gray) + program name
                            button_text = f"{child_label}{icon} {display_program}" + (" 💖" if in_schedule else "")

                            # Display provider name above button (smaller, gray text)
                            st.markdown(f'<div style="font-size: 0.75rem; color: #6c757d; margin-bottom: 4px;">{display_provider}</div>', unsafe_allow_html=True)
                            
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
    st.session_state.selected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
if 'selected_interests' not in st.session_state:
    st.session_state.selected_interests = []
# Removed alternative grid options - keeping standard view only
if 'child_age' not in st.session_state:
    st.session_state.child_age = 5
if 'grade_level' not in st.session_state:
    st.session_state.grade_level = 'K'
if 'program_types' not in st.session_state:
    st.session_state.program_types = ['On-site', 'Off-site']
if 'start_time' not in st.session_state:
    st.session_state.start_time = "02:00 PM"
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
if 'show_create_schedule' not in st.session_state:
    st.session_state.show_create_schedule = False  # True when showing create schedule dialog
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
if 'save_context_schedule' not in st.session_state:
    st.session_state.save_context_schedule = None

# Professional Theme & Schedule Grid Styling
st.markdown("""
<style>
/* MODERN FRIENDLY THEME SYSTEM */
:root {
    --primary-color: #1E3D59;
    --primary-color-light: #2E5D79;
    --primary-color-dark: #0E2D49;
    --secondary-color: #FEFEFE;
    --accent-color: #EBF8FF;
    --text-color: #2D3748;
    --border-color: #E2E8F0;
    --shadow: 0 3px 12px rgba(30, 61, 89, 0.12);
    --font-size-small: 0.875rem;
    --font-size-base: 1rem;
    --font-size-large: 1.125rem;
    --font-size-xl: 1.25rem;
    --font-size-xxl: 1.5rem;
    --font-size-header: 2.2rem;
    --distance-color: #FFD4A3;
    --availability-color: #38A169;
    --warm-background: #FEFEFE;
}

/* ORIGINAL NAVY THEME */
.stApp, .main, [data-testid="stAppViewContainer"] {
    background-color: var(--warm-background) !important;
    color: var(--text-color) !important;
}

/* MAIN HEADER */
.main-header {
    font-size: var(--font-size-header) !important;
    text-align: center !important;
    margin-bottom: 2rem !important;
    font-weight: 600 !important;
    color: var(--primary-color) !important;
    text-shadow: 0 1px 2px rgba(30, 61, 89, 0.1) !important;
}

/* PROGRAM CARD STYLING */
.program-card-container {
    background-color: #ffffff !important;
    color: var(--text-color) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 0.3rem;
    box-shadow: var(--shadow);
}

.program-card-title {
    color: var(--primary-color) !important;
    font-weight: 600 !important;
    margin-bottom: 0.2rem;
    font-size: var(--font-size-xl) !important;
}

.program-card-info-bar {
    background: #e8f4f8 !important;
    border-radius: 8px;
    padding: 0.7rem;
    margin-bottom: 0.8rem;
    border-left: 4px solid var(--primary-color);
}

.program-card-text {
    font-size: var(--font-size-base) !important;
    margin-bottom: 0.25rem;
}

.program-card-secondary {
    font-size: var(--font-size-small) !important;
    color: #6c757d !important;
    margin-bottom: 0.25rem;
}

/* SCHEDULE GRID BUTTONS */
.stButton button {
    background: white !important;
    color: var(--text-color) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
    font-size: var(--font-size-small) !important;
    font-weight: 500 !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
    min-height: 40px !important;
}

.stButton button:hover {
    border-color: var(--primary-color) !important;
    background: var(--secondary-color) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow) !important;
}

/* SAVED PROGRAM INDICATOR */
.program-selected button {
    border-left: 3px solid var(--accent-color) !important;
    background: rgba(40, 167, 69, 0.05) !important;
}

/* MOBILE RESPONSIVE */
@media (max-width: 768px) {
    .main-header {
        font-size: var(--font-size-xxl) !important;
    }
    
    .stButton button {
        min-height: 44px !important;
        padding: 10px 14px !important;
        font-size: var(--font-size-base) !important;
    }
    
    .program-card-title {
        font-size: var(--font-size-large) !important;
    }
}
</style>
""", unsafe_allow_html=True)

# App header with subtitle
st.markdown("""
<div style='text-align: center; margin-bottom: 2rem;'>
    <h1 class='main-header' style='font-size: 2.2rem; color: var(--primary-color) !important; line-height: 1.2; font-weight: 600; margin-bottom: 0.5rem;'>📚 After-School Program Finder</h1>
    <p style='font-size: 0.95rem; color: #64748B; margin: 0;'>Programs for Ages 3-5 (Grades 3K-K) in <strong style="color: #475569;">PS 38, Brooklyn</strong></p>
</div>
""", unsafe_allow_html=True)

# Load data
try:
    df = load_and_process_data("attached_assets/ProgramData.csv")

    # Filter to show only programs with spots open (hide waitlist and full programs)
    def has_spots_open(program):
        availability_status, _ = get_availability_status(program)
        return availability_status == "Spots Open"

    df = df[df.apply(has_spots_open, axis=1)].reset_index(drop=True)

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
        st.markdown('<div style="font-size: var(--font-size-large); font-weight: 600; color: var(--primary-color); margin: 1.5rem 0 0.75rem 0; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem;">👶 Child Information</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            child_age = st.number_input(
                "Child's Age",
                min_value=3,
                max_value=5,
                value=st.session_state.child_age,
                help="Programs available for ages 3-5"
            )
        with col2:
            # Grade level options for on-site programs (constrained to 3K-K)
            grade_options = ['3K', 'UPK', 'K']
            grade_level = st.selectbox(
                "Child's Grade Level",
                options=grade_options,
                index=grade_options.index(st.session_state.grade_level) if st.session_state.grade_level in grade_options else 2,
                help="Select grade level for on-site school programs (optional)"
            )

        # Program Location filter as checkboxes
        st.markdown('<div style="font-size: var(--font-size-large); font-weight: 600; color: var(--primary-color); margin: 1.5rem 0 0.75rem 0; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem;">📍 Program Location</div>', unsafe_allow_html=True)

        program_type_col1, program_type_col2 = st.columns(2)
        with program_type_col1:
            on_site_checked = st.checkbox(
                "On-site (School-based)",
                value='On-site' in st.session_state.program_types,
                key="on_site_checkbox",
                help="• On-site: School-based programs by World Explorers • Off-site: External venues"
            )
        with program_type_col2:
            off_site_checked = st.checkbox(
                "Off-site (External locations)",
                value='Off-site' in st.session_state.program_types,
                key="off_site_checkbox"
            )

        # Build program_types list based on checkboxes
        program_types = []
        if on_site_checked:
            program_types.append('On-site')
        if off_site_checked:
            program_types.append('Off-site')

        # Program Interests
        st.markdown('<div style="font-size: var(--font-size-large); font-weight: 600; color: var(--primary-color); margin: 1.5rem 0 0.75rem 0; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem;">🎨 Program Interests</div>', unsafe_allow_html=True)
        selected_interests = st.multiselect(
            "What activities interest your child?",
            options=interest_categories,
            default=st.session_state.selected_interests,
            help="Select one or more categories that match your child's interests"
        )
        
        # Home Location Section
        st.markdown('<div style="font-size: var(--font-size-large); font-weight: 600; color: var(--primary-color); margin: 1.5rem 0 0.75rem 0; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem;">🏠 Home Location</div>', unsafe_allow_html=True)

        col1, col2 = st.columns([3, 1])
        with col1:
            user_address = st.text_input(
                "Home Address (Optional)",
                value=st.session_state.user_address,
                placeholder="123 Main St, Brooklyn, NY",
                help="Enter your home address to see distances and get a personalized map view"
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

        # Smart address completion - auto-append Brooklyn, NY if incomplete
        address_auto_completed = False
        if user_address and user_address.strip():
            # Check if address is missing state (doesn't contain "NY" or similar state abbreviations)
            has_state = any(state in user_address.upper() for state in ['NY', 'NEW YORK', 'NJ', 'CT', 'PA'])

            if not has_state:
                # Auto-append Brooklyn, NY
                user_address = user_address.strip() + ", Brooklyn, NY"
                address_auto_completed = True
                st.info("ℹ️ Auto-completed address to: **" + user_address + "**\n\nFor more accurate results, please enter your full address including city and state.")

        # Schedule Preferences Section
        st.markdown('<div style="font-size: var(--font-size-large); font-weight: 600; color: var(--primary-color); margin: 1.5rem 0 0.75rem 0; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem;">⏰ Schedule Preferences</div>', unsafe_allow_html=True)
        
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
        st.markdown('<div style="font-size: var(--font-size-large); font-weight: 600; color: var(--primary-color); margin: 1.5rem 0 0.75rem 0; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem;">📅 Days Available</div>', unsafe_allow_html=True)
        st.markdown("Select the days your child is available for programs:")
        
        # Create a mobile-friendly day selection interface with proper order
        selected_days = []
        
        for day in days_of_week:
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
            st.session_state.grade_level = grade_level
            st.session_state.program_types = program_types
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
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-color-dark) 100%);
                padding: 15px 20px;
                border-radius: 12px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 4px 12px rgba(30, 61, 89, 0.2);
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
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-color-dark) 100%);
                padding: 15px 20px;
                border-radius: 12px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 4px 12px rgba(30, 61, 89, 0.2);
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
                'grade_level': grade_level,
                'program_types': program_types,
                'selected_interests': selected_interests,
                'selected_days': selected_days,
                'start_time': start_time,
                'end_time': end_time,
                'user_address': user_address,
                'max_distance': max_distance
            }

            # Close program details modal when filters change
            current_filters_str = str(filters)
            if 'previous_filters' not in st.session_state:
                st.session_state.previous_filters = current_filters_str
            elif st.session_state.previous_filters != current_filters_str:
                # Filters changed - close the modal
                st.session_state.show_program_details = False
                st.session_state.previous_filters = current_filters_str

            filtered_df = filter_programs(df, filters)
            
            # Step 3: Loading schedules
            progress_container.markdown("""
            <div style="
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--primary-color-dark) 100%);
                padding: 15px 20px;
                border-radius: 12px;
                text-align: center;
                margin: 20px 0;
                box-shadow: 0 4px 12px rgba(30, 61, 89, 0.2);
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
                box-shadow: 0 4px 12px rgba(30, 61, 89, 0.2);
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
            color: var(--primary-color) !important;
            font-size: var(--font-size-xxl) !important;
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
            
            # Clean Navigation Container
            with st.container():
                st.markdown("""
                <style>
                .navigation-container {
                    background: white !important;
                    padding: 20px !important;
                    border: 1px solid var(--border-color) !important;
                    border-radius: 12px !important;
                    margin-bottom: 24px !important;
                    box-shadow: var(--shadow) !important;
                }
                </style>
                """, unsafe_allow_html=True)

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
                    font-size: 1rem !important;
                    font-weight: 600 !important;
                    color: #1E3D59 !important;
                    margin: 0 0 15px 0 !important;
                    padding: 0 !important;
                    text-align: center;
                }
                
                /* Reduce map font sizes */
                .leaflet-container {
                    font-size: 11px !important;
                }
                
                .leaflet-control-zoom a {
                    font-size: 14px !important;
                }
                
                .leaflet-control-attribution {
                    font-size: 9px !important;
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
                        font-size: 0.9rem !important;
                    }
                    
                    .leaflet-container {
                        font-size: 10px !important;
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
                
                # Add program markers with larger, enhanced popups
                for prog_coords, program in program_coords:
                    # Create enhanced popup with larger size and more information
                    if 'Distance' in program and not pd.isna(program['Distance']):
                        popup_html = f"""
                        <div style="font-size: 14px; width: 280px; padding: 8px;">
                            <div style="font-size: 16px; font-weight: bold; color: #1E3D59; margin-bottom: 8px; line-height: 1.3;">{program['Program Name']}</div>
                            <div style="font-size: 13px; color: #333; margin-bottom: 6px;"><strong>Provider:</strong> {program['Provider Name']}</div>
                            <div style="font-size: 13px; color: #333; margin-bottom: 6px;"><strong>Distance:</strong> {program['Distance']:.2f} miles</div>
                            {f'<div style="font-size: 13px; color: #333; margin-bottom: 6px;"><strong>Ages:</strong> {program["Ages"]}</div>' if program.get('Ages') else ''}
                        </div>
                        """
                    else:
                        popup_html = f"""
                        <div style="font-size: 14px; width: 280px; padding: 8px;">
                            <div style="font-size: 16px; font-weight: bold; color: #1E3D59; margin-bottom: 8px; line-height: 1.3;">{program['Program Name']}</div>
                            <div style="font-size: 13px; color: #333; margin-bottom: 6px;"><strong>Provider:</strong> {program['Provider Name']}</div>
                            <div style="font-size: 13px; color: #333; margin-bottom: 6px;"><strong>Address:</strong> {program['Address']}</div>
                            {f'<div style="font-size: 13px; color: #333; margin-bottom: 6px;"><strong>Ages:</strong> {program["Ages"]}</div>' if program.get('Ages') else ''}
                        </div>
                        """
                    
                    # Create popup with increased max width
                    popup = folium.Popup(
                        html=popup_html,
                        max_width=320,
                        show=False
                    )
                    
                    folium.Marker(
                        prog_coords,
                        popup=popup,
                        icon=folium.Icon(color="blue", icon="info-circle", prefix="fa"),
                    ).add_to(m)
                
                # Responsive map sizing - optimized height for mobile
                map_height = 350  # Reduced height for mobile optimization
                st_folium(m, width="100%", height=map_height, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
        
        # Display results in schedule view format with enhanced empty states
        if len(filtered_df) > 0:
            # View Toggle and Schedule Display
            st.markdown("""
            <style>
            .schedule-view-header {
                font-size: var(--font-size-xxl) !important;
                font-weight: 600 !important;
                color: var(--primary-color) !important;
                margin: 1rem 0 0.5rem 0 !important;
                text-align: center !important;
            }
            .schedule-instruction {
                font-size: var(--font-size-base) !important;
                color: #6c757d !important;
                margin-bottom: 1rem !important;
                text-align: center !important;
                font-style: italic !important;
            }
            /* Mobile clickable program cards */
            .stButton button[key*="mobile_card"] {
                background: white !important;
                border: 2px solid var(--border-color) !important;
                border-radius: 12px !important;
                padding: 20px !important;
                margin: 10px 0 !important;
                box-shadow: var(--shadow) !important;
                transition: all 0.2s ease !important;
                text-align: left !important;
                white-space: pre-line !important;
                font-weight: 500 !important;
                line-height: 1.5 !important;
                color: var(--text-color) !important;
                min-height: auto !important;
                width: 100% !important;
            }
            
            .stButton button[key*="mobile_card"]:hover {
                border-color: var(--primary-color) !important;
                box-shadow: 0 6px 20px rgba(30, 61, 89, 0.2) !important;
                transform: translateY(-2px) !important;
                background: #fafafa !important;
            }
            
            /* Mobile save button styling */
            .stButton button[key*="mobile_save"] {
                background: var(--primary-color) !important;
                color: white !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                text-align: center !important;
                padding: 12px !important;
                margin: 10px 0 20px 0 !important;
            }
            .mobile-card-header {
                font-size: var(--font-size-xl);
                font-weight: 600;
                color: var(--primary-color);
                margin-bottom: 8px;
                line-height: 1.3;
            }
            .mobile-card-time {
                font-size: var(--font-size-base);
                font-weight: 500;
                color: var(--text-color);
                margin-bottom: 12px;
            }
            .mobile-card-details {
                font-size: var(--font-size-base);
                color: var(--text-color);
                margin-bottom: 15px;
                line-height: 1.5;
            }
            .mobile-card-buttons {
                display: flex;
                gap: 10px;
                margin-top: 15px;
            }
            .mobile-btn {
                flex: 1;
                padding: 12px;
                border-radius: 8px;
                font-weight: 600;
                text-align: center;
                text-decoration: none;
                transition: all 0.2s ease;
                min-height: 44px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .view-toggle {
                text-align: center;
                margin-bottom: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 10px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Initialize view mode in session state - default to Desktop Timetable View
            if 'view_mode' not in st.session_state:
                st.session_state.view_mode = 'Desktop Timetable View'
            
            # Streamlined view toggle
            st.markdown('<div class="view-toggle">', unsafe_allow_html=True)
            view_mode = st.radio(
                "View:",
                options=['📱 Mobile View', '🖥️ Desktop Timetable View'],
                index=1 if st.session_state.view_mode == 'Desktop Timetable View' else 0,
                horizontal=True,
                key="view_toggle"
            )
            
            # Update session state to handle both old and new naming
            if view_mode == '🖥️ Desktop Timetable View':
                st.session_state.view_mode = 'Desktop Timetable View'
            else:
                st.session_state.view_mode = 'Mobile View'
            
            st.markdown('</div>', unsafe_allow_html=True)

            # Schedule Pills Navigation - appears after view toggle
            st.markdown("""
            <style>
            .schedule-pills {
                background: #f8f9fa;
                border-radius: 12px;
                padding: 1.2rem;
                margin: 1.5rem 0;
                border: 1px solid #e2e8f0;
            }
            .pills-label {
                font-size: 0.9rem;
                font-weight: 600;
                color: #64748B;
                margin-bottom: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            </style>
            """, unsafe_allow_html=True)

            st.markdown('<div class="schedule-pills">', unsafe_allow_html=True)
            st.markdown('<div class="pills-label">📚 VIEW:</div>', unsafe_allow_html=True)

            # Calculate how many pills we'll have
            num_schedules = len(st.session_state.saved_schedules)

            # Create dynamic columns - all pills in one row
            if num_schedules == 0:
                # Just "All Programs"
                pill_cols = st.columns([2, 2])
            else:
                # All programs + all schedule pills
                pill_cols = st.columns([1.2] + [1.2] * num_schedules)

            # "All Programs" pill
            with pill_cols[0]:
                if st.button("📚 All Programs",
                             key="pill_all",
                             use_container_width=True,
                             type="primary" if st.session_state.current_schedule == "All Programs" else "secondary"):
                    st.session_state.current_schedule = "All Programs"
                    st.rerun()

            # Schedule pills - show all schedules
            col_index = 1
            for schedule_name, programs in st.session_state.saved_schedules.items():
                if col_index < len(pill_cols):
                    with pill_cols[col_index]:
                        # Truncate schedule name to 20 characters for better display
                        display_name = schedule_name if len(schedule_name) <= 20 else schedule_name[:20] + "..."
                        pill_label = f"{display_name}\n({len(programs)} programs)"
                        if st.button(pill_label,
                                    key=f"pill_{schedule_name}",
                                    use_container_width=True,
                                    type="primary" if st.session_state.current_schedule == schedule_name else "secondary"):
                            st.session_state.current_schedule = schedule_name
                            st.rerun()
                    col_index += 1

            st.markdown('</div>', unsafe_allow_html=True)

            # Show schedule info if viewing a single schedule (simpler styling)
            if st.session_state.current_schedule != "All Programs" and st.session_state.current_schedule in st.session_state.saved_schedules:
                schedule_programs = st.session_state.saved_schedules[st.session_state.current_schedule]

                # Calculate total cost
                total_cost = 0
                for prog in schedule_programs:
                    if 'Cost Per Class' in prog and prog['Cost Per Class'] and not pd.isna(prog['Cost Per Class']):
                        total_cost += float(prog['Cost Per Class'])

                # Info display with Share button
                info_col, share_col = st.columns([4, 1])

                with info_col:
                    st.markdown(f"""
                    <div style='background: #f8f9fa;
                                padding: 0.8rem 1rem;
                                border-radius: 8px;
                                margin: 1rem 0;
                                border-left: 4px solid var(--primary-color);'>
                        <div style='font-size: 1rem; font-weight: 600; color: var(--text-color);'>
                            📅 {st.session_state.current_schedule}
                        </div>
                        <div style='font-size: 0.9rem; color: #64748B; margin-top: 0.3rem;'>
                            {len(schedule_programs)} programs • ${total_cost:,.2f}/week
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with share_col:
                    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
                    if st.button("📤 Share", key="share_schedule_btn", use_container_width=True):
                        st.session_state.show_share_text = True

                # Show shareable text when Share button clicked
                if st.session_state.get('show_share_text', False):
                    # Format schedule as text
                    share_text = f"📅 {st.session_state.current_schedule}\n"
                    share_text += f"{len(schedule_programs)} programs • ${total_cost:,.2f}/week\n"
                    share_text += "=" * 50 + "\n\n"

                    for prog in schedule_programs:
                        # Day and time
                        day = prog.get('Day of the week', 'N/A')
                        start_time = prog.get('Start time', 'N/A')
                        end_time = prog.get('End time', 'N/A')
                        share_text += f"{day} {start_time} - {end_time}\n"

                        # Program name and provider
                        program_name = prog.get('Program Name', 'N/A')
                        provider = prog.get('Provider Name', 'N/A')
                        share_text += f"{program_name} - {provider}\n"

                        # Description (if available)
                        description = prog.get('Description')
                        if description and not pd.isna(description) and str(description).strip():
                            share_text += f"{description}\n"

                        # Address
                        address = prog.get('Address', 'N/A')
                        share_text += f"{address}\n"

                        # Cost
                        cost = prog.get('Cost Per Class', prog.get('Cost', 0))
                        if cost and not pd.isna(cost):
                            share_text += f"${float(cost):,.2f}/week\n"

                        share_text += "\n"

                    # Display text with built-in copy button
                    st.markdown("**📋 Share this schedule:**")
                    st.code(share_text, language=None)

                    # Copy and Close buttons
                    copy_col, close_col = st.columns([1, 1])

                    with copy_col:
                        if st.button("📋 Copy to Clipboard", key="copy_share_text", use_container_width=True, type="primary"):
                            st.success("✅ Copied! You can now paste it in any messaging app.")

                    with close_col:
                        if st.button("✖️ Close", key="close_share_text", use_container_width=True):
                            st.session_state.show_share_text = False
                            st.rerun()

            if st.session_state.view_mode == 'Mobile View':
                # Mobile View Implementation
                display_mobile_schedule_view(filtered_df)
            else:
                # Desktop Timetable View
                current_schedule = st.session_state.get('current_schedule', 'Schedule')
                
                st.markdown('<div class="schedule-instruction">Click on any program card, then use 💾 Save to add to your child\'s schedule</div>', unsafe_allow_html=True)
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
