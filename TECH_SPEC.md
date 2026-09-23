# Dashboard Data Synchronization Tech Spec

## Objective

The Dashboard uses four data layers whose freshness can be assessed independently:

1. **Quotes**: refresh on manual request and once after the market close. On weekends, keep the most recent trading-day close.
2. **Institutional flow**: use the latest official TWSE T86 settlement date.
3. **Fundamentals and events**: synchronize at 15:00 Asia/Taipei with the latest TWSE OpenAPI monthly revenue, quarterly income statement, and margin data. Past earnings-call dates must be labeled as completed instead of continuing to display stale wording such as “this Friday”.
4. **Research score**: keep the weekly research snapshot and do not make it appear real-time merely because quotes changed.

## Data Contract

The top-level payload must contain:

- `updated_at`: quote payload generation time, retained for backward compatibility.
- `quote_updated_at`: quote-layer update time.
- `market_as_of`: quote reference date. During market hours this is the current trading date; outside market hours it is the most recent trading date.
- `quote_status`: complete only when all 11 tracked stocks have a valid fresh quote. A partial response must retain the previous published quote layer rather than advancing its date.
- `fundamental_updated_at`: last successful fundamentals synchronization time.
- `fundamental_checked_at`: time of the latest fundamentals synchronization attempt.
- `fundamental_as_of`: publication date represented by the fundamentals data.
- `fundamental_source`: fundamentals source and status.
- `institutional_as_of`: latest TWSE T86 settlement date.
- `research_updated_at`: research/weekly-review snapshot date.

Each stock's fundamentals fields must prefer the latest official synchronization. If an official endpoint fails, the previous verified value must be retained and the failure must be exposed in `fundamental_status` instead of replacing the value with an empty field.

The institutional layer advances only when T86 returns all 11 tracked stocks for one official settlement date. A partial or unavailable T86 response retains the previous verified institutional layer and exposes its status separately.

## Frontend Behavior

- On Dashboard load, treat the latest published payload as authoritative for institutional flow, fundamentals, events, research, and cache version. A locally persisted payload may overlay only a newer complete quote layer. Do not start a 30-second polling loop.
- On “Force refresh quotes”, request the live quote gateway and overlay only quote fields onto the latest published payload. Institutional flow changes only when the scheduled TWSE T86 11/11 settlement payload is published.
- If a manual refresh fails, preserve the last available data and show a failure message; never show a false success state.
- Show separate quote, institutional, fundamentals, and research timestamps near the Dashboard header.

## Acceptance Criteria

- All 11 tracked stocks have the latest available monthly revenue and quarterly indicators, or an explicit and explainable degraded status.
- Past earnings calls, including Hon Hai's August event, no longer display stale future wording.
- A manual refresh updates quotes; weekends show the latest trading-day close.
- The page makes no automatic 30-second refresh requests.
- Local Python tests, JSON structure validation, JavaScript syntax checks, and desktop/mobile browser checks pass.
