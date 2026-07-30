import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from app.core.config import settings
from datetime import datetime

SCOPES = ['https://www.googleapis.com/auth/calendar.events']

class CalendarService:
    @staticmethod
    def get_flow():
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI
        return flow

    @staticmethod
    def create_event(token_data, summary, description, start_time, end_time):
        try:
            creds_dict = json.loads(token_data)
            creds = Credentials.from_authorized_user_info(creds_dict, SCOPES)
            
            service = build('calendar', 'v3', credentials=creds)
            
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat() + 'Z',
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_time.isoformat() + 'Z',
                    'timeZone': 'UTC',
                },
            }
            
            event = service.events().insert(calendarId='primary', body=event).execute()
            return event
        except Exception as e:
            print(f"Error creating calendar event: {e}")
            return None

calendar_service = CalendarService()
