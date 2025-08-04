import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
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

# Custom CSS for styling with mobile responsiveness
st.markdown("""
    <style>
    /* Base styles */
    .main-header,
    h1.main-header,
    .stMarkdown .main-header {
        font-size: 2.2rem !important;
        color: #1E3D59 !important;
        text-align: center !important;
        margin-bottom: 2rem !important;
        line-height: 1.2 !important;
        white-space: nowrap !important;
        font-weight: 700 !important;
    }
    
    .section-header {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #1E3D59 !important;
        margin: 1.5rem 0 0.75rem 0 !important;
        border-bottom: 2px solid #e9ecef !important;
        padding-bottom: 0.5rem !important;
        display: block !important;
        visibility: visible !important;
    }
    
    .section-header * {
        color: #1E3D59 !important;
        visibility: visible !important;
    }
    
    /* Force visibility for all content inside section headers */
    div.section-header {
        color: #1E3D59 !important;
    }
    
    div.section-header > * {
        color: #1E3D59 !important;
    }
    
    /* Target Streamlit's markdown rendering specifically */
    .stMarkdown .section-header {
        color: #1E3D59 !important;
    }
    
    .stMarkdown .section-header * {
        color: #1E3D59 !important;
    }
    
    .form-section {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #e9ecef;
    }
    
    .result-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Enhanced button styling */
    .stButton button {
        background-color: #1E3D59;
        color: white;
        font-weight: 600;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        width: 100%;
        font-size: 1.1rem;
        border: none;
        transition: background-color 0.2s;
    }
    
    .stButton button:hover {
        background-color: #2a5490;
    }
    
    /* Form container - responsive */
    div.stForm > div[data-testid="stForm"] {
        max-width: 800px;
        margin: 0 auto;
        padding: 1.5rem;
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Days selection - improved layout */
    .days-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
        gap: 0.5rem;
        margin: 1rem 0;
    }
    
    .day-button {
        background: #f8f9fa;
        border: 2px solid #e9ecef;
        border-radius: 8px;
        padding: 0.5rem;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .day-button.selected {
        background: #1E3D59;
        color: white;
        border-color: #1E3D59;
    }
    
    /* Input field improvements */
    div[data-testid="stNumberInput"], 
    div[data-testid="stTextInput"], 
    div[data-testid="stSelectbox"],
    div[data-testid="stMultiSelect"] {
        margin-bottom: 1rem;
    }
    
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .main-header,
        h1.main-header,
        .stMarkdown .main-header {
            font-size: 1.8rem !important;
            margin-bottom: 1.5rem !important;
        }
        
        /* Form takes full width on mobile */
        div.stForm > div[data-testid="stForm"] {
            max-width: 100% !important;
            margin: 0;
            padding: 1rem !important;
            border-radius: 8px;
        }
        
        .form-section {
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        /* Stack columns vertically on mobile */
        div[data-testid="column"] {
            padding-left: 0 !important;
            padding-right: 0 !important;
            margin-bottom: 1rem;
        }
        
        /* Better mobile input sizing */
        div[data-testid="stNumberInput"], 
        div[data-testid="stTextInput"], 
        div[data-testid="stMultiSelect"] {
            max-width: 100% !important;
        }
        
        /* Days grid - 2 columns on mobile */
        .days-container {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }
        
        .day-button {
            padding: 0.75rem 0.5rem;
            font-size: 0.85rem;
        }
        
        /* Result cards on mobile */
        .result-card {
            padding: 1rem;
            margin-bottom: 0.75rem;
        }
        
        /* Button sizing on mobile */
        .stButton button {
            padding: 1rem 1.5rem;
            font-size: 1rem;
        }
    }
    
    @media (max-width: 480px) {
        .main-header,
        h1.main-header,
        .stMarkdown .main-header {
            font-size: 1.5rem !important;
        }
        
        div.stForm > div[data-testid="stForm"] {
            padding: 0.75rem !important;
        }
        
        .form-section {
            padding: 0.75rem;
        }
        
        .days-container {
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem;
        }
        
        .day-button {
            padding: 0.6rem 0.3rem;
            font-size: 0.8rem;
        }
    }
    
    /* Map responsiveness */
    .stMap {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Results section styling */
    .results-header {
        color: #1E3D59;
        font-size: 1.4rem;
        margin: 1rem 0 0.5rem 0;
        text-align: center;
        padding: 0.5rem;
        background: transparent;
        border: none;
    }
    
    /* Submit button section */
    .submit-section {
        margin-top: 2rem;
        padding-top: 1.5rem;
        border-top: 2px solid #e9ecef;
        text-align: center;
    }
    
    /* Mobile map adjustments */
    @media (max-width: 768px) {
        .stMap, iframe {
            height: 300px !important;
            min-height: 300px !important;
        }
        
        .results-header {
            font-size: 1.2rem;
            margin: 1.5rem 0 0.75rem 0;
            padding: 0.75rem;
        }
        
        .submit-section {
            margin-top: 1.5rem;
            padding-top: 1rem;
        }
    }
    
    @media (max-width: 480px) {
        .stMap, iframe {
            height: 250px !important;
            min-height: 250px !important;
        }
        
        .results-header {
            font-size: 1.1rem;
            padding: 0.5rem;
        }
    }
    
    /* Dark mode compatibility */
    @media (prefers-color-scheme: dark) {
        .main-header {
            color: #ffffff !important;
        }
        
        .form-section {
            background: #262730;
            border-color: #404040;
        }
        
        .result-card {
            background-color: #262730;
            border-color: #404040;
        }
        
        .day-button {
            background: #404040;
            border-color: #555;
            color: #fff;
        }
        
        .results-header {
            background: transparent;
            color: #ffffff !important;
            border: none;
        }
        
        .section-header,
        div.section-header,
        .stMarkdown .section-header {
            color: #ffffff !important;
            border-color: #555 !important;
        }
        
        .section-header *,
        div.section-header *,
        .stMarkdown .section-header * {
            color: #ffffff !important;
        }
        
        /* Target specific result text styling in dark mode only */
        body div[style*="font-size: 1.4rem"] {
            color: #ffffff !important;
        }
        
        body div[style*="font-size: 1.3rem"] {
            color: #ffffff !important;
        }
    }
    
    /* Streamlit dark theme specific overrides */
    .stApp[data-theme="dark"] .main-header,
    [data-testid="stAppViewContainer"][data-theme="dark"] .main-header {
        color: #ffffff !important;
    }
    
    /* Only target inline styles in dark mode */
    @media (prefers-color-scheme: dark) {
        div[style*="color: #1E3D59"] {
            color: #ffffff !important;
        }
    }
    
    .stApp[data-theme="dark"] div[style*="color: #1E3D59"],
    [data-testid="stAppViewContainer"][data-theme="dark"] div[style*="color: #1E3D59"] {
        color: #ffffff !important;
    }
    </style>
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
        
        st.markdown(f'<div style="color: #1E3D59; font-size: 1.4rem; margin: 1rem 0 0.5rem 0; text-align: center; padding: 0.5rem; font-weight: 600;">{result_text}</div>', unsafe_allow_html=True)
        
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
                if len(program_coords) > 1 or user_coords:
                    southwest = [min(lats), min(lons)]
                    northeast = [max(lats), max(lons)]
                    m.fit_bounds([southwest, northeast], padding=(20, 20))
                
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
                
                st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #1E3D59; margin: 0.2rem 0 0.2rem 0; padding: 0;">🗺️ Program Locations</div>', unsafe_allow_html=True)
                
                # Responsive map sizing
                map_container = st.container()
                with map_container:
                    st_folium(m, width="100%", height=400, use_container_width=True)
        
        # Display results in cards
        if len(filtered_df) > 0:
            st.markdown('<div style="font-size: 1.3rem; font-weight: 600; color: #1E3D59; margin: 0.2rem 0; padding: 0;">📋 Program Details</div>', unsafe_allow_html=True)
        else:
            st.info("💡 **Tips for better results:**\n- Try increasing the distance range\n- Select fewer interest categories\n- Adjust the time range\n- Check more days of the week")
        for _, program in filtered_df.iterrows():
            with st.container():
                html = f"""
                <div style='background-color: #f8f9fa; border-radius: 12px; padding: 1.25rem; margin-bottom: 1rem; border: 1px solid #e9ecef; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                    <h3 style='color: #1E3D59; font-weight: bold; margin-bottom: 0.2rem; font-size: 1.2rem;'>{program.get('Program Name', 'N/A')}</h3>
                    <p style='color: #1E3D59; font-weight: 600; margin-bottom: 0.6rem; font-size: 1.0rem;'>{program.get('Provider Name', 'N/A')}</p>
                    <div style='background: #e8f4f8; border-radius: 8px; padding: 0.7rem; margin-bottom: 0.8rem; border-left: 4px solid #1E3D59;'>
                        <p style='margin: 0.2rem 0; font-weight: 600; color: #1E3D59;'><span style='margin-right: 8px;'>⏰</span>{program.get('Day of the week', 'N/A')} • {program.get('Start time', 'N/A')} - {program.get('End time', 'N/A')}</p>"""
                # Add cost and distance to key info bar
                if 'Distance' in program and not pd.isna(program['Distance']):
                    html += f"<p style='margin: 0.2rem 0; font-weight: 600; color: #1E3D59;'><span style='margin-right: 8px;'>📍</span>{program['Distance']:.2f} miles away</p>"
                cost_info = []
                enrollment_type = program.get('Enrollment Type', '').strip() if isinstance(program.get('Enrollment Type'), str) else ''
                
                if 'Cost' in program and not pd.isna(program['Cost']):
                    base_cost = f"${program['Cost']:.2f}"
                    if enrollment_type:
                        # Add enrollment type context to make cost clearer
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
                    html += f"<p style='margin: 0.2rem 0; font-weight: 600; color: #1E3D59;'><span style='margin-right: 8px;'>💰</span>{' • '.join(cost_info)}</p>"
                html += "</div>"
                
                # Secondary details
                html += f"<p style='margin: 0.4rem 0; color: #555;'><span style='margin-right: 6px;'>👶</span><strong>Ages:</strong> {int(float(program.get('Min Age', 0)))} - {int(float(program.get('Max Age', 0)))}</p>"
                html += f"<p style='margin: 0.4rem 0; color: #555;'><span style='margin-right: 6px;'>🎯</span><strong>Category:</strong> {program.get('Interest Category', 'N/A')}</p>"
                html += f"<p style='margin: 0.4rem 0; color: #555;'><span style='margin-right: 6px;'>📍</span><strong>Address:</strong> {program.get('Address', 'N/A')}</p>"
                
                # Contact & additional info
                if 'Website' in program and not pd.isna(program['Website']):
                    html += f"<p style='margin: 0.4rem 0; color: #555;'><span style='margin-right: 6px;'>🌐</span><a href='{program['Website']}' target='_blank' style='color: #1E3D59; text-decoration: none; font-weight: 600;'>Website</a></p>"
                if 'Contact Phone' in program and not pd.isna(program['Contact Phone']):
                    html += f"<p style='margin: 0.4rem 0; color: #555;'><span style='margin-right: 6px;'>📞</span><strong>Phone:</strong> {program['Contact Phone']}</p>"
                if 'School Pickup From' in program and isinstance(program['School Pickup From'], str) and program['School Pickup From'].strip():
                    html += f"<p style='margin: 0.4rem 0; color: #555;'><span style='margin-right: 6px;'>🚌</span><strong>School pickup:</strong> {program['School Pickup From']}</p>"
                html += "</div>"
                st.markdown(html, unsafe_allow_html=True)
    
except Exception as e:
    st.error(f"Error: {str(e)}")
