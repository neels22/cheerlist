from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI(title="CheerList - Google Calendar Integration")

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

# OAuth scopes
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# In-memory storage for demo (use database in production)
user_credentials = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CheerList - Google Calendar</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { 
                font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; 
                padding: 16px; 
                max-width: 800px; 
                margin: 0 auto; 
            }
            .container { 
                text-align: center; 
                padding: 20px; 
            }
            button { 
                padding: 12px 24px; 
                border: none; 
                border-radius: 8px; 
                background: #4285f4; 
                color: white; 
                font-size: 16px; 
                cursor: pointer; 
                margin: 10px; 
            }
            button:hover { 
                background: #3367d6; 
            }
            .events { 
                text-align: left; 
                margin-top: 20px; 
                padding: 20px; 
                border: 1px solid #ddd; 
                border-radius: 8px; 
                background: #f9f9f9; 
            }
            .event { 
                padding: 10px 0; 
                border-bottom: 1px solid #eee; 
            }
            .event:last-child { 
                border-bottom: none; 
            }
            .status { 
                padding: 10px; 
                margin: 10px 0; 
                border-radius: 4px; 
                background: #e3f2fd; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>CheerList - Google Calendar Integration</h1>
            <p>Connect your Google Calendar to see your upcoming events</p>
            
            <div id="status" class="status">Ready to connect</div>
            
            <div>
                <button onclick="login()">Connect Google Calendar</button>
                <button onclick="getEvents()" id="eventsBtn" style="display:none;">Get My Events</button>
                <button onclick="logout()" id="logoutBtn" style="display:none;">Disconnect</button>
            </div>
            
            <div id="events" class="events" style="display:none;">
                <h3>Your Upcoming Events:</h3>
                <div id="eventsList"></div>
            </div>
        </div>

        <script>
            // Check if user is already logged in
            checkAuthStatus();
            
            async function checkAuthStatus() {
                try {
                    const response = await fetch('/auth/status');
                    const data = await response.json();
                    
                    if (data.authenticated) {
                        document.getElementById('status').textContent = 'Connected to Google Calendar';
                        document.getElementById('eventsBtn').style.display = 'inline-block';
                        document.getElementById('logoutBtn').style.display = 'inline-block';
                    }
                } catch (error) {
                    console.log('Not authenticated');
                }
            }
            
            function login() {
                window.location.href = '/auth/login';
            }
            
            async function getEvents() {
                try {
                    document.getElementById('status').textContent = 'Loading events...';
                    const response = await fetch('/events');
                    const data = await response.json();
                    
                    if (data.success) {
                        displayEvents(data.events);
                        document.getElementById('status').textContent = `Found ${data.events.length} events`;
                    } else {
                        document.getElementById('status').textContent = 'Error: ' + data.error;
                    }
                } catch (error) {
                    document.getElementById('status').textContent = 'Error loading events';
                    console.error(error);
                }
            }
            
            function displayEvents(events) {
                const eventsList = document.getElementById('eventsList');
                const eventsDiv = document.getElementById('events');
                
                if (events.length === 0) {
                    eventsList.innerHTML = '<p>No upcoming events found.</p>';
                } else {
                    eventsList.innerHTML = events.map(event => `
                        <div class="event">
                            <strong>${event.summary || '(No title)'}</strong><br>
                            <small>${event.start || 'No date'}</small>
                        </div>
                    `).join('');
                }
                
                eventsDiv.style.display = 'block';
            }
            
            async function logout() {
                try {
                    await fetch('/auth/logout', { method: 'POST' });
                    location.reload();
                } catch (error) {
                    console.error('Logout error:', error);
                }
            }
        </script>
    </body>
    </html>
    """

@app.get("/auth/login")
async def login():
    """Initiate Google OAuth login"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Google OAuth credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env file")
    
    print(f"DEBUG: Using redirect URI: {GOOGLE_REDIRECT_URI}")
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [GOOGLE_REDIRECT_URI]
            }
        },
        scopes=SCOPES
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    
    print(f"DEBUG: Generated authorization URL: {authorization_url}")
    return RedirectResponse(url=authorization_url)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    """Handle OAuth callback"""
    try:
        code = request.query_params.get('code')
        if not code:
            raise HTTPException(status_code=400, detail="Authorization code not provided")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [GOOGLE_REDIRECT_URI]
                }
            },
            scopes=SCOPES
        )
        flow.redirect_uri = GOOGLE_REDIRECT_URI
        
        # Exchange code for token
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store credentials (in production, use a database)
        user_credentials['default_user'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        return RedirectResponse(url="/?success=true")
        
    except Exception as e:
        return RedirectResponse(url="/?error=" + str(e))

@app.get("/auth/status")
async def auth_status():
    """Check if user is authenticated"""
    return {
        "authenticated": 'default_user' in user_credentials,
        "user": "default_user" if 'default_user' in user_credentials else None
    }

@app.post("/auth/logout")
async def logout():
    """Logout user"""
    if 'default_user' in user_credentials:
        del user_credentials['default_user']
    return {"message": "Logged out successfully"}

@app.get("/events")
async def get_events():
    """Get user's calendar events"""
    try:
        if 'default_user' not in user_credentials:
            raise HTTPException(status_code=401, detail="Not authenticated")
        
        # Create credentials object
        creds_data = user_credentials['default_user']
        credentials = Credentials(
            token=creds_data['token'],
            refresh_token=creds_data['refresh_token'],
            token_uri=creds_data['token_uri'],
            client_id=creds_data['client_id'],
            client_secret=creds_data['client_secret'],
            scopes=creds_data['scopes']
        )
        
        # Refresh token if needed
        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(GoogleRequest())
                # Update stored credentials
                user_credentials['default_user'].update({
                    'token': credentials.token,
                    'refresh_token': credentials.refresh_token
                })
        
        # Build Google Calendar service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Get events
        now = datetime.utcnow().isoformat() + 'Z'
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=10,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Format events for frontend
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            formatted_events.append({
                'summary': event.get('summary', 'No title'),
                'start': start,
                'description': event.get('description', '')
            })
        
        return {
            "success": True,
            "events": formatted_events,
            "count": len(formatted_events)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "events": []
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
