import streamlit as st
import duckdb
import pandas as pd
import leafmap.foliumap as leafmap
import os

# Set page configuration and theme
st.set_page_config(
    page_title="Tree Census App",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    .reportview-container .main .block-container{
        padding-top: 1rem;
    }
    .reportview-container .main {
        color: #31333f;
        background-color: #e8eef9;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    .btn-primary {
        background-color: #5c832f;
        border-color: #5c832f;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize DuckDB
def init_db():
    conn = duckdb.connect(database=':memory:', read_only=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trees (
            id INTEGER,
            species VARCHAR,
            height DOUBLE,
            diameter DOUBLE,
            health_status VARCHAR,
            date_planted DATE,
            latitude DOUBLE,
            longitude DOUBLE,
            photo_path VARCHAR,
            video_path VARCHAR
        )
    """)
    return conn

if 'db_conn' not in st.session_state:
    st.session_state['db_conn'] = init_db()

# Function to save uploaded files
def save_uploaded_file(uploaded_file, folder="uploads"):
    if uploaded_file is not None:
        if not os.path.exists(folder):
            os.makedirs(folder)
        file_path = os.path.join(folder, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

# Function to add a tree
def add_tree(id, species, height, diameter, health_status, date_planted, latitude, longitude, photo, video):
    photo_path = save_uploaded_file(photo)
    video_path = save_uploaded_file(video)
    st.session_state.db_conn.execute("""
        INSERT INTO trees VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (id, species, height, diameter, health_status, date_planted, latitude, longitude, photo_path, video_path))
    st.success(f"Tree with ID {id} added. Photo saved to {photo_path}, video saved to {video_path}.")

# Function to view trees
def view_trees():
    return pd.read_sql("SELECT * FROM trees", st.session_state.db_conn)

# Function to create map
def create_map():
    m = leafmap.Map(center=[19.7515, 75.7139], zoom=7, basemap='Stamen.Terrain')
    try:
        tree_data = pd.read_sql("SELECT * FROM trees WHERE latitude IS NOT NULL AND longitude IS NOT NULL", st.session_state.db_conn)
        for index, row in tree_data.iterrows():
            popup_message = (
                f"ID: {row['id']}<br>"
                f"Species: {row['species']}<br>"
                f"Height: {row['height']} meters<br>"
                f"Diameter: {row['diameter']} cm<br>"
                f"Health Status: {row['health_status']}<br>"
                f"Date Planted: {row['date_planted']}<br>"
                f"Latitude: {row['latitude']}<br>"
                f"Longitude: {row['longitude']}"
            )
            if row['photo_path']:
                popup_message += f"<br>Photo: <a href='{row['photo_path']}' target='_blank'>View</a>"
            if row['video_path']:
                popup_message += f"<br>Video: <a href='{row['video_path']}' target='_blank'>View</a>"
            
            m.add_marker(location=(row['latitude'], row['longitude']), popup=popup_message)
    except Exception as e:
        st.error(f"Error in loading map data: {e}")
    return m

# Layout for form
st.title("🌳 INDICES GEOSPATIAL TREE CENSUS APP 🌳")
with st.form("tree_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        tree_id = st.number_input("Tree ID", step=1)
        species = st.text_input("Species")
        height = st.number_input("Height (in meters)", step=0.1)
    with col2:
        diameter = st.number_input("Diameter (in cm)", step=0.1)
        health_status = st.selectbox("Health Status", ["Healthy", "Needs Attention", "Unhealthy"])
        date_planted = st.date_input("Date Planted")
    with col3:
        latitude = st.number_input("Latitude")
        longitude = st.number_input("Longitude")
        photo = st.file_uploader("Upload Tree Photo", type=['jpg', 'png', 'jpeg'])
        video = st.file_uploader("Upload Tree Video", type=['mp4', 'mov', 'avi'])

    submit_button = st.form_submit_button("Add Tree")
    if submit_button:
        add_tree(tree_id, species, height, diameter, health_status, date_planted, latitude, longitude, photo, video)

# View trees button
if st.button("View Trees"):
    trees = view_trees()
    if not trees.empty:
        st.write(trees)
    else:
        st.error("No trees found.")

# Display map
st.subheader("📍 Tree Locations on Map")
m = create_map()
m.to_streamlit(height=700)
