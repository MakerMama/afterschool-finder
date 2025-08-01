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
    </style>
""", unsafe_allow_html=True)

# App header
st.markdown("<h1 class='main-header'>📚 Find Your Perfect After-School Program</h1>", unsafe_allow_html=True)

# Load data with DEBUG INFO
try:
    df = load_and_process_data("attached_assets/ProgramData.csv")
    
    # DEBUG: Show data loading info
    st.sidebar.markdown("### 🔍 DEBUG INFO")
    st.sidebar.write(f"**Total programs loaded:** {len(df)}")
    st.sidebar.write(f"**Columns found:** {len(df.columns)}")
    
    # Show column names to check for issues
    st.sidebar.write("**Column names:**")
    for i, col in enumerate(df.columns):
        st.sidebar.write(f"{i+1}. '{col}' (len: {len(col)})")
    
    # Show sample data
    if len(df) > 0:
        st.sidebar.write("**First program data:**")
        first_program = df.iloc[0]
        for col in ['Program Name', 'Day of the week', 'Start time', 'End time', 'Min Age', 'Max Age']:
            if col in df.columns:
                st.sidebar.write(f"- {col}: '{first_program[col]}' (type: {type(first_program[col])})")
    
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
            
            # DEBUG: Show filter parameters
            st.write("### 🔍 FILTER DEBUG")
            st.write(f"**Child age:** {child_age}")
            st.write(f"**Selected days:** {selected_days}")
            st.write(f"**Selected interests:** {selected_interests}")
            st.write(f"**Time range:** {start_time} - {end_time}")
            st.write(f"**Address:** {user_address}")
            st.write(f"**Max distance:** {max_distance}")
            
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
            
            # DEBUG: Step by step filtering
            st.write("### 🔍 FILTERING STEPS")
            
            # Start with all programs
            test_df = df.copy()
            st.write(f"**Step 0 - All programs:** {len(test_df)}")
            
            # Days filter
            if selected_days:
                before = len(test_df)
                test_df = test_df[test_df['Day of the week'].isin(selected_days)]
                st.write(f"**Step 1 - After day filter:** {len(test_df)} (removed {before - len(test_df)})")
                if len(test_df) == 0:
                    st.error("❌ NO PROGRAMS LEFT after day filter!")
                    st.write(f"Available days in CSV: {df['Day of the week'].unique()}")
            
            # Age filter
            if child_age is not None:
                before = len(test_df)
                test_df = test_df[
                    (test_df['Min Age'] <= child_age) & 
                    (test_df['Max Age'] >= child_age)
                ]
                st.write(f"**Step 2 - After age filter:** {len(test_df)} (removed {before - len(test_df)})")
                if len(test_df) == 0:
                    st.error("❌ NO PROGRAMS LEFT after age filter!")
                    st.write(f"Age ranges in CSV: Min={df['Min Age'].min()}, Max={df['Max Age'].max()}")
            
            # Use the actual filter function
            filtered_df = filter_programs(df, filters)
            st.session_state.filtered_df = filtered_df
            
            st.write(f"**Final result:** {len(filtered_df)} programs")
        else:
            st.session_state.filtered_df = None
            st.session_state.submitted = False

    # Show results if form was submitted
    if st.session_state.submitted and st.session_state.filtered_df is not None:
        filtered_df = st.session_state.filtered_df
        
        # Show number of results
        st.subheader(f"Found {len(filtered_df)} programs matching your criteria")
        
        # Create map if address is provided
        if st.session_state.user_address and len(filtered_df) > 0:
            user_coords = geocode_address(st.session_state.user_address)
            if user_coords:
                m = folium.Map(location=user_coords, zoom_start=13)
                # Add user marker
                folium.Marker(
                    user_coords,
                    popup="Your Location",
                    icon=folium.Icon(color="red", icon="home"),
                ).add_to(m)
                # Add program markers
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
        # DEBUG: Show what's actually in the first filtered program
        if len(filtered_df) > 0:
            st.write("### 🔍 FIRST PROGRAM RAW DATA")
            first_result = filtered_df.iloc[0]
            for col in ['Day of the week', 'Start time', 'End time', 'Min Age', 'Max Age', 'Interest Category', 'Address']:
                if col in first_result:
                    st.write(f"**{col}:** '{first_result[col]}' (type: {type(first_result[col])}, null: {pd.isna(first_result[col])})")
                    
        for _, program in filtered_df.iterrows():
            with st.container():
                st.write(f"🔍 BUILDING CARD FOR: {program.get('Program Name', 'UNKNOWN')}")
                html = f"""
                    <div style='background: lightgray; padding: 10px; margin: 10px;'>
                        <h3>TEST PROGRAM</h3>
                        <p>Name: {program.get('Program Name', 'N/A')}</p>
                        <p>Day: {program.get('Day of the week', 'N/A')}</p>
                    </div>
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
        st.session_state.filtered_df = None
        st.session_state.submitted = False
    
except Exception as e:
    st.error(f"Error: {str(e)}")
    import traceback
    st.write("**Full error traceback:**")
    st.code(traceback.format_exc())
