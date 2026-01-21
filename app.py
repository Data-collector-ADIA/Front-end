"""
Streamlit Frontend for Data Collector ADIA
Provides a web interface for managing browser automation tasks.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import grpc
import streamlit as st

# Add parent directory to path to import generated protobuf files
# Get the directory where app.py is located
app_file_path = Path(__file__).resolve()
app_dir = app_file_path.parent  # Should be /Users/macbook/Front-end
parent_dir = app_dir.parent      # Should be /Users/macbook

# Verify we're going in the right direction
if not app_dir.name == "Front-end":
    # If not in Front-end directory, try different approach
    # This might happen if Streamlit is running from a different location
    import os
    cwd = Path(os.getcwd()).resolve()
    if (cwd / "app.py").exists():
        app_dir = cwd
        parent_dir = cwd.parent
    else:
        # Last resort: look for Front-end directory
        for potential_path in [Path.home() / "Front-end", Path("/Users/macbook/Front-end")]:
            if (potential_path / "app.py").exists():
                app_dir = potential_path
                parent_dir = app_dir.parent
                break

sys.path.insert(0, str(parent_dir))

# Import generated protobuf files - these are required for gRPC communication
try:
    import backend_service_pb2
    import backend_service_pb2_grpc
    import database_service_pb2
    import database_service_pb2_grpc
except ImportError as e:
    # Try to generate them if they're missing
    shared_dir = parent_dir / "shared"
    
    # Debug: show what we're looking for
    if not shared_dir.exists():
        st.error(f"❌ shared_dir not found at: {shared_dir}\n\nDEBUG INFO:\n__file__: {__file__}\napp_file_path: {app_file_path}\napp_dir: {app_dir}\nparent_dir: {parent_dir}")
        st.stop()
    
    generate_script = shared_dir / "generate_protos.py"
    if not generate_script.exists():
        st.error(f"❌ generate_protos.py not found at: {generate_script}")
        st.stop()
    
    try:
        # Run generate script
        result = subprocess.run(
            [sys.executable, str(generate_script)],
            cwd=str(shared_dir),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise Exception(f"Generation failed: {result.stderr}")
        
        # Copy generated files to parent directory
        import shutil
        for proto_file in shared_dir.glob("*_pb2*.py"):
            shutil.copy(proto_file, parent_dir)
        
        # Clear the import cache and try again
        for mod in ['backend_service_pb2', 'backend_service_pb2_grpc', 
                   'database_service_pb2', 'database_service_pb2_grpc']:
            if mod in sys.modules:
                del sys.modules[mod]
        
        import backend_service_pb2
        import backend_service_pb2_grpc
        import database_service_pb2
        import database_service_pb2_grpc
    except Exception as gen_error:
        st.error(f"⚠️ Failed to generate protobuf files.\n\nError: {gen_error}")
        st.stop()

# Configuration
BACKEND_SERVICE_HOST = os.getenv("BACKEND_SERVICE_HOST", "localhost")
BACKEND_SERVICE_PORT = int(os.getenv("BACKEND_SERVICE_PORT", "50050"))
DATABASE_SERVICE_HOST = os.getenv("DATABASE_SERVICE_HOST", "localhost")
DATABASE_SERVICE_PORT = int(os.getenv("DATABASE_SERVICE_PORT", "50052"))

# Page configuration
st.set_page_config(
    page_title="Data Collector ADIA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .task-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin-bottom: 1rem;
    }
    .status-running { color: #ff9800; }
    .status-completed { color: #4caf50; }
    .status-failed { color: #f44336; }
    .status-pending { color: #2196f3; }
    </style>
""", unsafe_allow_html=True)


def get_backend_client():
    """Get gRPC client for Backend Service"""
    try:
        channel = grpc.insecure_channel(
            f"{BACKEND_SERVICE_HOST}:{BACKEND_SERVICE_PORT}",
            options=[('grpc.keepalive_time_ms', 10000)]
        )
        # Try to verify the connection
        grpc.channel_ready_future(channel).result(timeout=2)
        return backend_service_pb2_grpc.BackendServiceStub(channel)
    except Exception as e:
        st.warning(f"⚠️ Backend Service unavailable at {BACKEND_SERVICE_HOST}:{BACKEND_SERVICE_PORT}")
        st.info("To use the full app, please start the backend service with: `python server.py`")
        return None


def get_database_client():
    """Get gRPC client for Database Service"""
    try:
        channel = grpc.insecure_channel(
            f"{DATABASE_SERVICE_HOST}:{DATABASE_SERVICE_PORT}",
            options=[('grpc.keepalive_time_ms', 10000)]
        )
        # Try to verify the connection
        grpc.channel_ready_future(channel).result(timeout=2)
        return database_service_pb2_grpc.DatabaseServiceStub(channel)
    except Exception as e:
        st.warning(f"⚠️ Database Service unavailable at {DATABASE_SERVICE_HOST}:{DATABASE_SERVICE_PORT}")
        st.info("To use the full app, please start the database service.")
        return None


def format_timestamp(timestamp):
    """Format Unix timestamp to readable date"""
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
    return "N/A"


def get_status_color(status):
    """Get color for status badge"""
    colors = {
        "running": "🟠",
        "completed": "🟢",
        "failed": "🔴",
        "pending": "🔵",
        "cancelled": "⚫"
    }
    return colors.get(status.lower(), "⚪")


# Main App
st.markdown('<div class="main-header">🤖 Data Collector ADIA</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select Page",
        ["Create Task", "Task List", "Task History"],
        index=0
    )
    
    st.divider()
    st.header("Service Status")
    
    # Check backend service
    try:
        backend_client = get_backend_client()
        st.success("✓ Backend Service: Connected")
    except Exception as e:
        st.error(f"✗ Backend Service: {str(e)}")
    
    # Check database service
    try:
        db_client = get_database_client()
        st.success("✓ Database Service: Connected")
    except Exception as e:
        st.error(f"✗ Database Service: {str(e)}")


# Page: Create Task
if page == "Create Task":
    st.header("Create New Task")
    
    with st.form("create_task_form"):
        task_prompt = st.text_area(
            "Task Prompt",
            placeholder="Enter the task you want the AI agent to perform...",
            height=150
        )
        
        col1, col2 = st.columns(2)
        with col1:
            max_steps = st.number_input("Max Steps", min_value=1, max_value=1000, value=15)
        with col2:
            browser_name = st.selectbox("Browser", ["firefox", "webkit", "chrome"], index=2)
        
        user_id = st.text_input("User ID (optional)", value="default")
        
        submitted = st.form_submit_button("Start Task", type="primary")
        
        if submitted:
            if not task_prompt:
                st.error("Please enter a task prompt")
            else:
                try:
                    backend_client = get_backend_client()
                    
                    if backend_client is None:
                        st.error("❌ Cannot start task: Backend service is not available")
                        st.info("Please start the backend service first.")
                    else:
                        request = backend_service_pb2.StartTaskRequest(
                            task_prompt=task_prompt,
                            max_steps=max_steps,
                            user_id=user_id,
                            browser_name=browser_name
                        )
                        
                        with st.spinner("Starting task..."):
                            response = backend_client.StartTask(request)
                        
                        if response.success:
                            st.success(f"Task started successfully! Task ID: {response.task_id}")
                            st.info(f"Message: {response.message}")
                            st.session_state['last_task_id'] = response.task_id
                        else:
                            st.error(f"Failed to start task: {response.message}")
                            
                except grpc.RpcError as e:
                    st.error(f"gRPC Error: {e.code()} - {e.details()}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")


# Page: Task List
elif page == "Task List":
    st.header("Task List")
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        filter_user_id = st.text_input("Filter by User ID (optional)", value="")
    with col2:
        refresh_button = st.button("🔄 Refresh", type="secondary")
    
    try:
        db_client = get_database_client()
        
        if db_client is None:
            st.error("❌ Cannot load tasks: Database service is not available")
            st.info("Please start the database service first.")
        else:
            request = database_service_pb2.ListTasksRequest(
                user_id=filter_user_id if filter_user_id else "",
                limit=100,
                offset=0
            )
            
            with st.spinner("Loading tasks..."):
                response = db_client.ListTasks(request)
            
            if response.tasks:
                st.metric("Total Tasks", response.total)
                
                for task in response.tasks:
                    with st.expander(
                        f"{get_status_color(task.status)} {task.task_prompt[:50]}... | Status: {task.status.upper()}",
                        expanded=False
                    ):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**Task ID:** `{task.task_id}`")
                            st.write(f"**Status:** {task.status}")
                            st.write(f"**Max Steps:** {task.max_steps}")
                            st.write(f"**User ID:** {task.user_id}")
                        
                        with col2:
                            st.write(f"**Created:** {format_timestamp(task.created_at)}")
                            st.write(f"**Updated:** {format_timestamp(task.updated_at)}")
                        
                        if task.final_result:
                            st.json(json.loads(task.final_result))
                        
                        # View history button
                        if st.button(f"View History", key=f"history_{task.task_id}"):
                            st.session_state['selected_task_id'] = task.task_id
                            st.rerun()
            else:
                st.info("No tasks found. Create a new task to get started!")
            
    except grpc.RpcError as e:
        st.error(f"gRPC Error: {e.code()} - {e.details()}")
    except Exception as e:
        st.error(f"Error loading tasks: {str(e)}")


# Page: Task History
elif page == "Task History":
    st.header("Task History")
    
    # Get task ID from session state or input
    task_id = st.text_input(
        "Task ID",
        value=st.session_state.get('selected_task_id', ''),
        placeholder="Enter task ID to view history"
    )
    
    if task_id:
        try:
            db_client = get_database_client()
            
            request = database_service_pb2.GetTaskHistoryRequest(task_id=task_id)
            
            with st.spinner("Loading task history..."):
                response = db_client.GetTaskHistory(request)
            
            if response.success and response.outputs:
                st.success(f"Found {len(response.outputs)} output(s)")
                
                # Display task info
                task_request = database_service_pb2.GetTaskRequest(task_id=task_id)
                task_response = db_client.GetTask(task_request)
                
                if task_response.success:
                    task = task_response.task
                    st.info(f"**Task:** {task.task_prompt} | **Status:** {task.status}")
                
                # Display outputs
                for output in response.outputs:
                    with st.expander(
                        f"Step {output.step_number} - {output.output_type} ({format_timestamp(output.timestamp)})",
                        expanded=False
                    ):
                        try:
                            step_data = json.loads(output.step_data)
                            st.json(step_data)
                        except json.JSONDecodeError:
                            st.text(output.step_data)
            else:
                st.warning("No history found for this task")
                
        except grpc.RpcError as e:
            st.error(f"gRPC Error: {e.code()} - {e.details()}")
        except Exception as e:
            st.error(f"Error loading history: {str(e)}")
    else:
        st.info("Enter a task ID to view its history")


# Footer
st.divider()
st.markdown(
    "<div style='text-align: center; color: #666;'>Data Collector ADIA - Browser Automation System</div>",
    unsafe_allow_html=True
)

