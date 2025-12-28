# Frontend Service - Quick Start

Get the Streamlit Frontend running quickly for testing or production deployment.

## Prerequisites

- Python 3.11+
- Backend Service running (port 50050)
- Database Service running (port 50052)

## Quick Setup

### 1. Install Dependencies

```bash
cd Front-end
pip install -r requirements.txt
```

### 2. Generate Protobuf Files (First Time Only)

```bash
cd ../shared
python generate_protos.py
cd ../Front-end
```

## Running the Service

You have two options for the frontend:

### Option 1: Streamlit App (Recommended)

Run in a screen session:

```bash
# Create a new screen session
screen -S frontend-service

# Start Streamlit
streamlit run app.py

# Detach: Press Ctrl+A then D
# Reattach: screen -r frontend-service
```

### Option 2: HTML Frontend with gRPC Proxy

If you prefer the HTML interface:

```bash
# Create a new screen session
screen -S frontend-service

# Start proxy server (handles HTML + gRPC conversion)
python proxy_server.py

# Detach: Press Ctrl+A then D
# Reattach: screen -r frontend-service
```

**Note:** The `server.py` file now automatically redirects to `proxy_server.py` for full gRPC support.

### For Production (Separate Machine)

```bash
# Set environment variables
export BACKEND_SERVICE_HOST=backend-service-host
export BACKEND_SERVICE_PORT=50050
export DATABASE_SERVICE_HOST=database-service-host
export DATABASE_SERVICE_PORT=50052

# Run Streamlit
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

## Access the UI

Open your browser and navigate to:

```
http://localhost:8501
```

## Configuration

### Environment Variables

```bash
BACKEND_SERVICE_HOST=localhost          # Backend Service host (default: localhost)
BACKEND_SERVICE_PORT=50050              # Backend Service port (default: 50050)
DATABASE_SERVICE_HOST=localhost         # Database Service host (default: localhost)
DATABASE_SERVICE_PORT=50052             # Database Service port (default: 50052)
```

### Streamlit Configuration

Create `.streamlit/config.toml` for custom settings:

```toml
[server]
port = 8501
address = "0.0.0.0"

[browser]
gatherUsageStats = false
```

### Default Ports

- **Streamlit UI**: `8501`
- **Backend Service**: `50050` (remote)
- **Database Service**: `50052` (remote)

## Features

- **Create Task**: Submit browser automation tasks
- **Task List**: View all tasks with status indicators
- **Task History**: View detailed execution history
- **Real-time Updates**: Status updates via polling

## Troubleshooting

### Cannot Connect to Backend Service

```bash
# Verify Backend Service is running
grpcurl -plaintext localhost:50050 list

# Check environment variables
echo $BACKEND_SERVICE_HOST
echo $BACKEND_SERVICE_PORT
```

### Cannot Connect to Database Service

```bash
# Verify Database Service is running
grpcurl -plaintext localhost:50052 list

# Check environment variables
echo $DATABASE_SERVICE_HOST
echo $DATABASE_SERVICE_PORT
```

### Protobuf Import Errors

```bash
# Regenerate protobuf files
cd ../shared
python generate_protos.py
```

### Port Already in Use

```bash
# Check what's using the port
lsof -i :8501  # Linux/Mac
netstat -an | findstr 8501  # Windows

# Change port
streamlit run app.py --server.port=8502
```

### Streamlit Not Found

```bash
# Install Streamlit
pip install streamlit
```

## Using the UI

### Create a Task

1. Navigate to "Create Task" page
2. Enter task prompt (e.g., "Search for browser automation on DuckDuckGo")
3. Set max steps (default: 100)
4. Select browser type
5. Click "Start Task"

### View Tasks

1. Navigate to "Task List" page
2. See all tasks with status indicators
3. Click "View History" to see execution details

### View Task History

1. Navigate to "Task History" page
2. Enter task ID or select from list
3. View step-by-step execution details

## Next Steps

- See [README.md](README.md) for detailed documentation
- Customize the UI for your needs
- Configure for production deployment

