# Bloomberg API Behavior Documentation

## Critical Discovery - July 30, 2025

### Investigation Summary
Through collaborative investigation with user and confirmation from engineering team, we discovered the true behavior of the Bloomberg API on the Azure VM.

### Key Finding: Terminal UI vs API Connection Separation

**The Bloomberg Python API connection persists independently of Terminal UI state**

#### How it Works:
1. **Initial Login**: User logs into Bloomberg Terminal UI during the day
2. **API Activation**: This login activates the Python API connection 
3. **Terminal Timeout**: Terminal UI logs off after inactivity (security feature)
4. **API Persistence**: Python connection REMAINS ACTIVE and continues serving real data
5. **Data Continuity**: API serves real Bloomberg data even when Terminal UI shows login screen

#### Evidence:
- API returned today's USDCNHV1M value (2.9575) before Terminal was loaded
- This exact value matched Terminal when loaded later
- JPY OIS curve data was available with full historical data
- Engineers confirmed this is expected behavior

#### Architecture:
```
User Action                    System Response
-----------                    ---------------
Login to Terminal UI     →     Activates both Terminal + API sessions
Terminal UI timeout      →     Only Terminal UI disconnects
API continues running    →     Serves cached + live data
Re-login to Terminal     →     Refreshes data feeds
```

#### Implications for Development:
1. **High Availability**: API provides data continuity beyond Terminal sessions
2. **Real Data**: The data is real Bloomberg data, not fallback values
3. **Cache Behavior**: Some data refreshes immediately, some remains cached
4. **Security Model**: API authentication persists longer than UI for operational continuity

### Technical Details:
- API Server: Python process on port 8080 (Azure VM)
- Uses Bloomberg Server API (SAPI) or B-PIPE
- Independent session management from Terminal UI
- Maintains connection for extended periods after Terminal UI logout

### Discovered by:
- User observation: "Terminal was off yesterday" but data was available
- Systematic testing: Values before/after Terminal load
- Engineering confirmation: "If you log during the day on the terminal then the python connection keeps alive"

This behavior is a FEATURE, not a bug - designed for production system reliability.