# Heartbeat Endpoint Setup Guide

## Overview
The heartbeat endpoint keeps your Render app active by preventing cold starts and database sleep. It's a lightweight endpoint that returns a 200 OK status.

## Endpoint Details
- **URL**: `https://your-app.onrender.com/heartbeat/`
- **Method**: GET or POST
- **Response**: `{"status": "ok", "timestamp": "2026-01-14T..."}` (200 OK)
- **No Authentication Required**: Uses `@csrf_exempt` decorator

## Setup Options

### Option 1: UptimeRobot (Recommended - Free)
1. Go to [UptimeRobot.com](https://uptimerobot.com)
2. Sign up for a free account
3. Click "Add New Monitor"
4. Configure:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: CLAS Heartbeat
   - **URL**: `https://your-app.onrender.com/heartbeat/`
   - **Monitoring Interval**: 5 minutes
   - **HTTP Method**: GET
5. Save and activate

### Option 2: Cron Job (Linux/Mac)
Run this command to edit your crontab:
```bash
crontab -e
```

Add this line to ping every 5 minutes:
```bash
*/5 * * * * curl -s https://your-app.onrender.com/heartbeat/ > /dev/null 2>&1
```

### Option 3: GitHub Actions (Free)
Create `.github/workflows/heartbeat.yml`:
```yaml
name: Heartbeat

on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes

jobs:
  heartbeat:
    runs-on: ubuntu-latest
    steps:
      - name: Ping heartbeat endpoint
        run: curl -s https://your-app.onrender.com/heartbeat/
```

## Testing
Test the endpoint manually:
```bash
curl https://your-app.onrender.com/heartbeat/
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2026-01-14T15:30:45.123456Z"
}
```

## Benefits
✅ Prevents Render from spinning down your app  
✅ Keeps database connections active  
✅ Eliminates cold start delays  
✅ Lightweight - minimal resource usage  
✅ No authentication required  

## Notes
- The endpoint is CSRF-exempt for easy external pinging
- Pinging every 5 minutes is sufficient to keep the app active
- No database queries are performed - purely a status check
- Works with any HTTP client (curl, wget, Postman, etc.)
