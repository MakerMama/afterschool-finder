import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from datetime import datetime
from utils import filter_programs, geocode_address, load_and_process_data, get_unique_values

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

# Custom CSS for styling
st.markdown("""
    <style>
    .main-header {
        font-size: 1.5rem;
        color: #1E3D59;
        text-align: center;
        margin-bottom: 1.5rem;
        white-space: nowrap;
        overflow: hidden;
        width: 100%;
    }
    .result-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
    }
    .program-name {
        color: #1E3D59;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 0.5rem;
    }
    .provider-name {
        color: #555;
        font-style: italic;
        margin-bottom: 0.5rem;
    }
    .info-label {
        font-weight: bold;
        color: #495057;
    }
    .stButton button {
        background-color: #1E3D59;
        color: white;
        font-weight: 600;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    /* Form container - narrower width */
    div.stForm > div[data-testid="stForm"] {
        max-width: 600px !important;
        margin: 0 auto;
        padding: 2rem;
    }
    /* Day picker container */
    div.day-picker {
        display: flex;
        flex-wrap: nowrap;
        justify-content: space-between;
        padding: 0;
        margin: 0;
        flex-wrap: nowrap;
        width: 100%;
        max-width: 500px;
    }
    /* Make day checkboxes more compact */
    div.row-widget.stCheckbox {
        display: inline-block;
        margin: 0;
        min-width: 10px;
        padding: 0;
    }
    /* Day checkbox styling */
    div.stCheckbox > label {
        white-space: nowrap;
        font-size: 0.75rem;
        padding: 0;
        margin: 0;
    }
    /* Reduce column padding */
    div[data-testid="column"] {
        padding-left: 2px !important;
        padding-right: 2px !important;
    }
    /* Input fields - reduced width */
    div[data-testid="stNumberInput"] {
        max-width: 150px;
    }
    div[data-testid="stTextInput"] {
        max-width: 400px;
    }
    /* Multiselect field - reduced width */
    div[data-testid="stMultiSelect"] {
        max-width: 400px;
    }
    </style>
""", unsafe_allow_html=True)

# App header
st.markdown("<h1 class='main-header'>📚 Find Your Perfect After-School Program</h1>", unsafe_allow_html=True)

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

    # Create form
    with st.form(key='program_filter_form'):
        # Two columns for first row
        col1, col2 = st.columns(2)
        
        with col1:
            # Child's age input
            child_age = st.number_input(
                "Child's age",
                min_value=0,
                max_value=18,
                value=st.session_state.child_age,
                help="Enter your child's age to find age-appropriate programs"
            )
        with col2:
            max_distance = st.number_input(
                "Distance (mi)",
                min_value=0.1,
                max_value=100.0,
                value=float(st.session_state.max_distance),
                step=0.5,
                help="Maximum distance from your location"
            )
        
        # Time range
        time_col1, time_col2 = st.columns(2)
        with time_col1:
            start_time = st.selectbox(
                "Start Time",
                options=time_options,
                index=time_options.index(st.session_state.start_time),
                help="Earliest program start time"
            )
        with time_col2:
            # Select default end time index, ensuring it's not out of bounds
            end_time_index = time_options.index(st.session_state.end_time) if st.session_state.end_time in time_options else len(time_options) - 1
            end_time = st.selectbox(
                "End Time",
                options=time_options,
                index=end_time_index,
                help="Latest program end time"
            )
        
        # Address input
        user_address = st.text_input(
            "Your Address",
            value=st.session_state.user_address,
            help="Enter your full address to calculate distances"
        )
        
        # Interest categories
        selected_interests = st.multiselect(
            "Interest Categories",
            options=interest_categories,
            default=st.session_state.selected_interests,
            help="Select program categories that interest your child"
        )
        
        # Days of week
        st.write("Days Available")
        # Use columns to layout the checkboxes horizontally
        days_columns = st.columns(7)
        selected_days = []
        
        for i, day in enumerate(days_of_week):
            with days_columns[i]:
                if st.checkbox(day[:3], value=day in st.session_state.selected_days, key=f"day_{day}"):
                    selected_days.append(day)
        
        # Submit button
        submitted = st.form_submit_button(label="Find Programs")
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
        else:
            # If form is not submitted, clear previous results and submission state
            st.session_state.filtered_df = None
            st.session_state.submitted = False

    # Show results if form was submitted
    if st.session_state.submitted and st.session_state.filtered_df is not None:
        filtered_df = st.session_state.filtered_df
        
        # Show number of results
        st.subheader(f"Found {len(filtered_df)} programs matching your criteria")
        # Create map if address is provided
        if st.session_state.user_address and len(filtered_df) > 0:
            # Clear previous map by recreating a new folium map object each timefolium_static
            user_coords = geocode_address(st.session_state.user_address)
            if user_coords:
                m = folium.Map(location=user_coords, zoom_start=13)
                # Add user marker
                folium.Marker(
                    user_coords,
                    popup="Your Location",
                    icon=folium.Icon(color="red", icon="home"),
                ).add_to(m)
                # Add program markers (no accumulation from previous runs)
                for _, program in filtered_df.iterrows():
                    prog_coords = geocode_address(program['Address'])
                    if prog_coords:
                        popup_html = f"""
                        <strong>{program['Program Name']}</strong><br>
                        {program['Provider Name']}<br>
                        Distance: {program['Distance']:.2f} miles
                        """
                        folium.Marker(
                            prog_coords,
                            popup=popup_html,
                            icon=folium.Icon(color="blue", icon="info-sign"),
                        ).add_to(m)
                st.subheader("Programs Near You")
                folium_static(m)
        
        # Display results in cards
        st.subheader("Program Details")
        for _, program in filtered_df.iterrows():
            with st.container():
                html = f"""
                <div class='result-card'>
                    <div class='program-name'>{program['Program Name']}</div>
                    <div class='provider-name'>{program['Provider Name']}</div>
                    <p><span class='info-label'>Day:</span> {program['Day of the week']}</p>
                    <p><span class='info-label'>Time:</span> {program['Start time']} - {program['End time']}</p>
                    <p><span class='info-label'>Ages:</span> {int(program['Min Age'])} - {int(program['Max Age'])}</p>
                    <p><span class='info-label'>Category:</span> {program['Interest Category']}</p>
                    <p><span class='info-label'>Address:</span> {program['Address']}</p>
                """
                if 'Distance' in program:
                    html += f"<p><span class='info-label'>Distance:</span> {program['Distance']:.2f} miles</p>"
                if 'Cost' in program and not pd.isna(program['Cost']):
                    html += f"<p><span class='info-label'>Cost:</span> ${program['Cost']:.2f}</p>"
                if 'Cost Per Class' in program and not pd.isna(program['Cost Per Class']):
                    html += f"<p><span class='info-label'>Cost Per Class:</span> ${program['Cost Per Class']:.2f}</p>"
                if 'Website' in program and not pd.isna(program['Website']):
                    html += f"<p><span class='info-label'>Website:</span> <a href='{program['Website']}' target='_blank'>Visit Website</a></p>"
                if 'Contact Phone' in program and not pd.isna(program['Contact Phone']):
                    html += f"<p><span class='info-label'>Phone:</span> {program['Contact Phone']}</p>"
                if 'School Pickup From' in program and isinstance(program['School Pickup From'], str) and program['School Pickup From'].strip():
                    html += f"<p><span class='info-label'>School Pickup:</span> {program['School Pickup From']}</p>"
                if 'Enrollment Type' in program and isinstance(program['Enrollment Type'], str) and program['Enrollment Type'].strip():
                    html += f"<p><span class='info-label'>Enrollment Type:</span> {program['Enrollment Type']}</p>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
        
    else:
        # Reset filtered_df and submitted if form is not submitted
        st.session_state.filtered_df = None
        st.session_state.submitted = False
    
except Exception as e:
    st.error(f"Error: {str(e)}")
