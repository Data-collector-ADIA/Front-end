"""
Frontend Service - HTTP server with gRPC proxy support
Serves HTML interface and proxies API calls to gRPC services

This file now redirects to proxy_server.py for full functionality.
For best results, run: python proxy_server.py
"""

import os
import sys

# Redirect to proxy_server.py for full functionality
if __name__ == "__main__":
    print("=" * 60)
    print("NOTE: server.py is being redirected to proxy_server.py")
    print("For full gRPC support, use: python proxy_server.py")
    print("=" * 60)
    print()
    
    # Import and run proxy_server
    try:
        from proxy_server import serve
        port = int(os.getenv("FRONTEND_SERVICE_PORT", "8501"))
        serve(port)
    except ImportError as e:
        print(f"ERROR: Could not import proxy_server: {e}")
        print("Please make sure proxy_server.py exists in the same directory.")
        print("Alternatively, use Streamlit: streamlit run app.py")
        sys.exit(1)

