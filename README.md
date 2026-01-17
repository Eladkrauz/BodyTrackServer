# BodyTrack – Backend Server

## Overview
This repository contains the backend server of the BodyTrack system – a real-time posture analysis and feedback platform developed as part of a final software engineering project.

The server is responsible for receiving video frames from the mobile client, analyzing body posture using a processing pipeline, managing training sessions, and returning feedback decisions to the client in real time.

## System Role
The backend server acts as the central processing unit of the system.
Its main responsibilities include:
- Managing active training sessions
- Receiving video frames from the Android client
- Running posture analysis and validation logic
- Tracking historical frame data for stable decision making
- Generating posture feedback and session summaries

The server is designed to be stateful, handling each user session independently while maintaining performance suitable for real-time interaction.

## Technologies Used
- Python 3
- Flask – HTTP API and request routing
- Gunicorn – production-grade WSGI server
- Systemd – service management
- Linux (Ubuntu) – deployment environment

## Project Structure (Simplified)
```
Server/
│
├── Server.py                 # Main entry point (Flask app)
├── Management/               # Session and test management
├── Pipeline/                 # Posture analysis pipeline
├── Config/                   # Configuration and parameters
├── Utils/                    # Shared utilities and definitions
└── README.md                 # This file
```

The internal structure follows a layered design, separating request handling, session management, processing logic, and configuration.

## Requirements
- Python 3.9+
- Linux-based environment (recommended)
- Virtual environment support (venv)
- Network access (HTTP)

## Installation
Clone the repository:
```
git clone <repository-url>
cd Server
```

Create and activate a virtual environment:
```
python3 -m venv venv
source venv/bin/activate
```

Install required dependencies:
```
pip install -r requirements.txt
```

## Running the Server
### Development Mode
For local development and testing:
```
source venv/bin/activate
python Server.py
```

The server listens on:
- Host: 0.0.0.0
- Port: 8080

This mode is intended for debugging and development only.

### Production Mode (Gunicorn)
For production deployment, the server is executed using Gunicorn, which runs the Flask application as a managed process:
```
gunicorn Server:app --bind 0.0.0.0:8080
```

In production, the server is typically managed through a system service to ensure availability and automatic restarts.

## Service Management

In the deployed environment, the backend server runs as a system-managed service named: `bodytrack`

This service controls the Gunicorn process and allows standard lifecycle operations.


### Common Commands
- `sudo systemctl start bodytrack`
-`sudo systemctl stop bodytrack`
- `sudo systemctl restart bodytrack`
- `sudo systemctl status bodytrack`

These commands allow starting, stopping, and monitoring the server without manual process management.

### Logs and Monitoring
Runtime logs are automatically collected by the operating system’s logging system.
To view live server logs: `sudo journalctl -u bodytrack -f`

Logs include:
- Server startup information
- Runtime warnings
- Error messages
- Session-level issues

Log inspection is the primary method for diagnosing unexpected behavior.

## Configuration
System behavior is controlled through centralized configuration files and parameters.
Configuration allows:
- Adjusting thresholds
- Modifying timing values
- Tuning posture validation logic

Changes to configuration do not require modifications to the core processing pipeline, as long as the parameter structure is preserved.

## Notes on Security and Networking
The server currently communicates over HTTP using a public IP address.
Future improvements may include:
- HTTPS support
- Domain-based access
- Secure certificate configuration

These changes do not affect the internal processing pipeline.

## Intended Audience
This repository is intended for:
- Developers maintaining or extending the backend
- Academic reviewers evaluating system implementation
- Future contributors to the BodyTrack project

End users interact with the system through the mobile client, not directly with this server.

## Academic Context
This backend server was developed as part of a final capstone project in software engineering, with emphasis on:
- Real-time processing
- Clean architecture
- Maintainability

## Practical deployment considerations
For detailed design decisions, architecture diagrams, and evaluation results, refer to the accompanying project documentation.