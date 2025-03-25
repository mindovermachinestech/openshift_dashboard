import streamlit as st
import plotly.express as px
import pandas as pd
import time
import random
import openshift
import plotly.graph_objects as go
from openshift_agent import process_request
import urllib3

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Page configuration
st.set_page_config(page_title="OpenShift Dashboard", layout="wide")

# Sidebar Menu
menu = st.sidebar.radio("Menu", ["Application Dashboard", "Manage Deployments", "Deploy New Application"])

# Dummy application list
applications = openshift.get_applications()


def show_dashboard():
    st.header("Application Dashboard")
    app_selected = st.selectbox("Select Application:", applications)

    # Divide page into two columns
    col1, col2 = st.columns([3, 1])
    with col1:
        # Telemetry Data
        st.subheader(f"Telemetry Data for {app_selected}")
        tele_data_frame = openshift.get_telemetry_data(app_selected)
        st.write(tele_data_frame)
        #chart_placeholder = st.empty()
        #data = []
        #fig = px.line(tele_data_frame, x="Time", y=["CPU Usage (%)", "Memory Usage (%)"], title="Resource Usage")
        #chart_placeholder.plotly_chart(fig, use_container_width=True)
        # for i in range(10):
        #     new_data = {
        #         "Time": pd.Timestamp.now(),
        #         "CPU Usage (%)": random.randint(10, 90),
        #         "Memory Usage (%)": random.randint(20, 80)
        #     }
        #     data.append(new_data)
        #     df = pd.DataFrame(data)
        #     fig = px.line(df, x="Time", y=["CPU Usage (%)", "Memory Usage (%)"], title="Resource Usage")
        #     chart_placeholder.plotly_chart(fig, use_container_width=True)
        #     time.sleep(1)

        # Loop through each pod to create a box with bar chart
        # for index, row in tele_data_frame.iterrows():
        #     pod_name = row["Pod Name"]
        #     memory_usage = row["Memory Usage (Ki)"]
        #     cpu_usage = row["CPU Usage (m)"]
        #
        #     # Create Plotly bar chart
        #     fig = go.Figure(data=[
        #         go.Bar(name="Memory (KB)", x=["Memory"], y=[memory_usage], marker_color="blue"),
        #         go.Bar(name="CPU (mCPU)", x=["CPU"], y=[cpu_usage], marker_color="red"),
        #     ])
        #
        #     fig.update_layout(
        #         title=f"Resource Usage for {pod_name}",
        #         barmode="group",
        #         xaxis_title="Resource Type",
        #         yaxis_title="Usage",
        #         height=300,
        #     )
        #
        #     # Add custom CSS to reduce chart width
        #     st.markdown(
        #         """
        #         <style>
        #         .chart-container {
        #             width: 100px;  /* Set the desired width */
        #             margin: 0 auto;  /* Center the chart */
        #         }
        #         </style>
        #         """,
        #         unsafe_allow_html=True,
        #     )
        #
        #     # Create a box for each pod
        #     with st.container():
        #         st.markdown(f"### {pod_name}")
        #         st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        #         st.plotly_chart(fig, use_container_width=False)
        #         st.markdown("</div>", unsafe_allow_html=True)

        # Health Status
        st.subheader("Application Health Status")
        if app_selected:
            status_data = openshift.get_pods_for_application(app_selected)
            st.dataframe(status_data)
        else:
            status_data = pd.DataFrame({
                "Component": ["Pod1", "Pod2", "Pod3"],
                "Status": ["Running", "Pending", "Running"]
            })
            st.dataframe(status_data)

        # Log Streaming
        st.subheader("Application Logs")
        # Dropdown to select number of lines to tail
        # Add custom CSS to reduce the width of the select box
        st.markdown(
            """
            <style>
            div[data-baseweb="select"] {
                width: 150px !important;  /* Set desired width */
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        tail_lines = st.selectbox(
            "Select number of lines to tail:",
            [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
            index=1,  # Default to 20 lines
        )

        # Checkbox to stream logs
        stream_logs = st.checkbox("Stream Logs in Real-time")

        # Button to fetch or stream logs
        if st.button("Fetch Logs"):
            log_placeholder = st.empty()

            if stream_logs:
                lines = ""
                # Stream logs dynamically
                duration = 10  # Duration in seconds (can be modified if needed)
                for i in range(duration):
                    for log in openshift.get_application_logs(app_selected, tail_lines):
                        lines = lines + log
                        log_placeholder.code(lines, language="bash")
                        time.sleep(0.001)
            else:
                # Fetch logs normally
                logs = openshift.get_application_logs(app_selected, tail_lines)
                log_placeholder.code(logs, language="bash")


    with col2:
        st.subheader("AI Chatbot - Ask About Your Cluster")
        user_query = st.text_input("Ask a question about OpenShift:")
        if st.button("Ask Chatbot"):
            response = process_request(user_query)
            st.write(f"Response: {response}")


def manage_deployments():
    st.header("Manage Deployments")
    app_selected = st.selectbox("Select Application:", applications)
    action = st.selectbox(
        "Choose Action:",
        ["Scale", "Restart", "Upgrade", "Undeploy"]
    )
    if st.button("Execute Action"):
        st.success(f"Action '{action}' executed successfully on '{app_selected}'")

    st.subheader("AI Chatbot - Manage Deployments with Natural Language")
    user_query = st.text_input("Ask a question about managing deployments:")
    if st.button("Ask Chatbot"):
        st.write(f"Response: Simulated response to '{user_query}'")


def deploy_application():
    st.header("Deploy New Application")
    app_name = st.text_input("Application Name")
    project_name = st.text_input("Project Name")
    image_url = st.text_input("Image URL")
    if st.button("Deploy Application"):
        st.success(f"Application '{app_name}' deployed successfully in project '{project_name}'")


# Menu Routing
if menu == "Application Dashboard":
    show_dashboard()
elif menu == "Manage Deployments":
    manage_deployments()
elif menu == "Deploy New Application":
    deploy_application()
