# Frontend Service

The Frontend Service provides a web-based user interface for the Data Collector ADIA system. It allows users to create browser automation tasks, view task history, and monitor real-time task execution via WebSocket connections.

## Overview

This service provides:
- Web-based UI for task management
- Real-time task streaming via WebSocket
- Task history viewing
- Task creation and monitoring

## Features

- Modern, responsive UI design
- Real-time task updates via WebSocket
- Task history retrieval and display
- Task status visualization
- Step-by-step execution viewing

## Installation

### Prerequisites

- Python 3.11 or higher (optional - can serve via any web server)
- Backend Service running (port 8000)
- Database Service running (port 8002)

### Setup

**Option 1: Python HTTP Server**
```bash
python server.py
```

**Option 2: Any Web Server**

You can serve the `index.html` file using any web server:
- Nginx
- Apache
- Python's built-in HTTP server
- Node.js http-server
- Or open directly in browser (with CORS limitations)

## Usage

### Start the Service

Using Python server:
```bash
python server.py
```

Or with custom port:
```bash
FRONTEND_SERVICE_PORT=8003 python server.py
```

The service will start on `http://localhost:8003` by default.

### Access the UI

Open your browser and navigate to:
```
http://localhost:8003
```

## Configuration

### Backend URL

Update the `BACKEND_URL` in `index.html` if your services run on different ports:

```javascript
const BACKEND_URL = 'http://localhost:8000';  // Backend Service URL
```

The frontend automatically constructs Database Service URL from Backend URL (replacing port 8000 with 8002).

## Features

### Create Task

1. Enter task prompt (e.g., "Search for browser automation on DuckDuckGo")
2. Set max steps (default: 100)
3. Select browser (Firefox, Chrome, WebKit)
4. Click "Start Task"
5. Task will appear in the output panel and start streaming

### View Task History

- Task list shows all tasks with status badges
- Click any task to view its history
- Tasks are sorted by creation date (newest first)

### Monitor Real-time Execution

- When a task starts, WebSocket connection is established
- Real-time updates appear in the output panel
- Each step shows:
  - Step number
  - Current URL
  - Agent thinking
  - Actions taken
  - Results

### Task Status Colors

- 🟡 **Pending** - Task created but not started
- 🔵 **Running** - Task is currently executing
- 🟢 **Completed** - Task finished successfully
- 🔴 **Failed** - Task encountered an error
- ⚪ **Cancelled** - Task was cancelled

## UI Components

### Left Panel - Task Management

- **Task Creation Form**: Create new automation tasks
- **Task History List**: Browse and select previous tasks

### Right Panel - Task Output

- **Stream Output**: Real-time execution updates
- **Step Details**: Detailed information about each step
- **Final Results**: Task completion summary

## WebSocket Integration

The frontend connects to the Backend Service WebSocket endpoint:

```javascript
ws://localhost:8000/tasks/{task_id}/stream
```

Connection is automatically established when:
- A new task is created
- An existing running task is selected

### Message Types

The frontend handles these message types:

- `task_start` - Task initialization
- `step` - Step-by-step execution updates
- `task_complete` - Task completion
- `error` - Error notifications

## API Integration

### Backend Service Endpoints

- `POST /tasks/start` - Create and start task
- `GET /tasks/{id}/status` - Get task status
- `WebSocket /tasks/{id}/stream` - Real-time updates

### Database Service Endpoints

- `GET /tasks` - List all tasks
- `GET /tasks/{id}` - Get task details
- `GET /tasks/{id}/history` - Get task execution history

## Customization

### Styling

Edit the `<style>` section in `index.html` to customize:
- Colors
- Layout
- Typography
- Component styles

### Backend URL

Change the backend URL in the script section:
```javascript
const BACKEND_URL = 'http://your-backend-url:8000';
```

## Architecture

The frontend is a single-page application (SPA) that:
- Uses vanilla JavaScript (no framework dependencies)
- Communicates with backend via REST APIs
- Receives real-time updates via WebSocket
- Stores no client-side state (stateless design)

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- WebSocket support required
- ES6+ JavaScript features

## Troubleshooting

### Cannot Connect to Backend

- Verify Backend Service is running on port 8000
- Check CORS settings in Backend Service
- Verify firewall/network rules

### WebSocket Connection Fails

- Ensure WebSocket endpoint is accessible
- Check browser console for errors
- Verify task ID is valid

### Tasks Not Loading

- Verify Database Service is running on port 8002
- Check browser console for API errors
- Verify CORS headers are set correctly

### No Updates Appearing

- Check WebSocket connection status
- Verify task is actually running
- Check browser console for errors

## Development

### Project Structure
```
Front-end/
├── index.html   # Main HTML/JS/CSS file
├── server.py    # Python HTTP server (optional)
└── README.md   # This file
```

### Adding Features

To add new features:

1. **New API Endpoint**: Update JavaScript functions in `index.html`
2. **New UI Component**: Add HTML/CSS in `index.html`
3. **New WebSocket Message**: Update `formatOutput()` function

### Testing

1. Start all services (Browser, Database, Backend)
2. Start Frontend service
3. Open browser to `http://localhost:8003`
4. Create a test task
5. Monitor execution in real-time

## Deployment

### Production Deployment

For production:

1. Serve via a proper web server (Nginx, Apache)
2. Configure CORS properly
3. Use HTTPS for WebSocket connections
4. Set proper cache headers
5. Minify JavaScript/CSS

### Docker Deployment

You can containerize the frontend:
```dockerfile
FROM nginx:alpine
COPY index.html /usr/share/nginx/html/
EXPOSE 80
```

## License

Part of the Data Collector ADIA project.

