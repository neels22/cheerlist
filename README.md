# CheerList - Google Calendar Integration

A Python FastAPI backend that integrates with Google Calendar API, replacing the original JavaScript frontend-only implementation.

## Architecture Change

**Before (JavaScript Frontend-only):**
- Browser directly calls Google APIs
- OAuth handled in browser
- No backend server

**After (Python FastAPI Backend):**
- Frontend makes requests to your FastAPI backend
- Backend handles Google API calls
- Backend manages OAuth flow
- Traditional request-response pattern

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google Calendar API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set application type to "Web application"
6. Add authorized redirect URI: `http://localhost:8000/auth/callback`
7. Download the credentials JSON file

### 3. Environment Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your Google OAuth credentials in `.env`:
   ```
   GOOGLE_CLIENT_ID=your_client_id_from_google_console
   GOOGLE_CLIENT_SECRET=your_client_secret_from_google_console
   GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
   SECRET_KEY=any_random_string_for_security
   ```

### 4. Run the Application

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the Application

Open your browser and go to: `http://localhost:8000`

## How It Works

### Request-Response Flow

1. **User clicks "Connect Google Calendar"**
   - Frontend redirects to `/auth/login`
   - Backend redirects to Google OAuth
   - User authorizes on Google
   - Google redirects back to `/auth/callback`
   - Backend stores OAuth tokens

2. **User clicks "Get My Events"**
   - Frontend makes GET request to `/events`
   - Backend uses stored tokens to call Google Calendar API
   - Backend returns formatted events to frontend
   - Frontend displays events

### API Endpoints

- `GET /` - Main page (HTML)
- `GET /auth/login` - Start OAuth flow
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/status` - Check authentication status
- `POST /auth/logout` - Logout user
- `GET /events` - Get calendar events

### Key Differences from Original

1. **Server-side OAuth**: Tokens are stored on the server, not in browser
2. **API-based**: Frontend communicates with backend via HTTP requests
3. **Secure**: Client secrets are never exposed to browser
4. **Scalable**: Can easily add features like user management, data persistence

## Development

### Adding New Features

1. **New API endpoint**: Add route in `main.py`
2. **Database integration**: Replace in-memory storage with database
3. **User management**: Add user registration/login system
4. **Additional Google APIs**: Extend the service calls

### Production Deployment

1. Use a proper database (PostgreSQL, MongoDB)
2. Set up environment variables securely
3. Use HTTPS for OAuth redirects
4. Add proper error handling and logging
5. Deploy to cloud platform (Heroku, AWS, etc.)

## Troubleshooting

- **OAuth errors**: Check redirect URI matches exactly
- **API errors**: Verify Google Calendar API is enabled
- **Token errors**: Tokens expire, user needs to re-authenticate
- **CORS issues**: FastAPI handles CORS automatically

## Next Steps

1. Add user authentication system
2. Implement database storage
3. Add more calendar features (create events, etc.)
4. Add error handling and validation
5. Deploy to production