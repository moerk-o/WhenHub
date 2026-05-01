# Technical Reference: Home Assistant Integration `whenhub`

**Version:** 2.4.0
**Date:** May 2026
**Target Platform:** Home Assistant Custom Integration
**Development Language:** English (code, comments, variables)
**Translations:** English (fallback), German
**Repository:** https://github.com/moerk-o/WhenHub

---

## 1. Project Overview

### 1.1 Purpose

**The origin story:** The kids kept asking "How much longer until vacation?" or "How many days until my birthday?". WhenHub was created to answer these questions by displaying countdown information on Home Assistant dashboards - showing an image of the event with the remaining days prominently displayed.

WhenHub provides:

- Multiple event types for different use cases (trips, milestones, anniversaries, holidays, custom patterns)
- Countdown sensors with days until/since calculations
- Binary sensors for "is today" detection
- Image entities for visual event representation
- Breakdown attributes for localized countdown text (years, months, weeks, days)
- URL and Memo sensors for optional metadata
- Calendar entity to aggregate events in the HA calendar view
- Expiry notifications via HA Repairs (opt-in)
- Full UI configuration via ConfigFlow

### 1.2 Event Types Overview

| Event Type | Key | Key Feature |
|------------|-----|-------------|
| **Trip** | `trip` | Start/End dates, progress tracking |
| **Milestone** | `milestone` | Single target date, can be in the past |
| **Anniversary** | `anniversary` | Yearly recurrence, leap year handling, occurrence counting |
| **Special Event** | `special` | Holidays + DST + Custom Pattern (dateutil.rrule) |
| **Calendar** | `calendar` | Aggregates WhenHub events in the HA calendar view |

### 1.3 Naming Convention

- **Domain:** `whenhub`
- **Entity Prefix:** User-defined event name (e.g., "Denmark Vacation" → `sensor.denmark_vacation_*`)
- **Entity ID Suffix:** Always the English sensor type key, regardless of HA system language (e.g., `days_until`, not `tage_bis_start`). Enforced via `suggested_object_id` since v3.0.0.
- **Unique ID Pattern:** `{entry_id}_{sensor_type}`

---

## 2. Calculation Logic

All calculations are implemented in pure Python without external dependencies (except Custom Pattern which uses `dateutil.rrule` — bundled in HA). The `calculations.py` module contains deterministic functions that take explicit date parameters for testability.

### 2.1 Basic Date Calculations

#### Days Until/Since

```python
def days_until(target_date: date, today: date) -> int:
    return (target_date - today).days
```

Returns negative values when the target date is in the past. This is intentional - a milestone that has passed still shows how many days ago it occurred.

#### Countdown Breakdown

For building localized countdown text, WhenHub provides breakdown attributes:

```python
def countdown_breakdown(target_date: date, today: date) -> dict[str, int]:
    total_days = (target_date - today).days

    years = total_days // 365
    remaining = total_days - (years * 365)

    months = remaining // 30
    remaining = remaining - (months * 30)

    weeks = remaining // 7
    days = remaining % 7

    return {"years": years, "months": months, "weeks": weeks, "days": days}
```

**Approximations used:**
- 1 year = 365 days
- 1 month = 30 days

These approximations provide consistent, predictable results. For exact calendar calculations, the slight inaccuracy is acceptable since the primary use case is countdown display.

### 2.2 Trip Calculations

Trip events have both a start and end date, requiring additional calculations.

#### Trip Progress Percentage

```python
def trip_left_percent(start_date: date, end_date: date, today: date) -> float:
    total_days = (end_date - start_date).days

    if today < start_date:
        return 100.0  # Trip hasn't started
    elif today > end_date:
        return 0.0    # Trip is over
    else:
        passed_days = (today - start_date).days
        remaining_percent = 100.0 - ((passed_days / total_days) * 100.0)
        return round(remaining_percent, 1)
```

| Phase | `trip_left_percent` |
|-------|---------------------|
| Before trip | 100.0 |
| During trip | Decreasing from ~100 to ~0 |
| After trip | 0.0 |

#### Trip Left Days

Returns remaining days only when the trip is active:

```python
def trip_left_days(start_date: date, end_date: date, today: date) -> int:
    if start_date <= today <= end_date:
        return (end_date - today).days + 1  # Including today
    return 0
```

### 2.3 Anniversary Calculations

Anniversary events handle the complexity of yearly recurrence, including leap year edge cases.

#### Leap Year Handling

When the original anniversary date is February 29th, non-leap years use February 28th:

```python
def anniversary_for_year(original_date: date, target_year: int) -> date:
    try:
        return original_date.replace(year=target_year)
    except ValueError:
        # Feb 29 in non-leap year -> use Feb 28
        return date(target_year, 2, 28)
```

**Example:**
- Original date: February 29, 2020 (leap year)
- Anniversary 2021: February 28, 2021
- Anniversary 2024: February 29, 2024 (leap year)

#### Next/Last Anniversary

```python
def next_anniversary(original_date: date, today: date) -> date:
    this_year = anniversary_for_year(original_date, today.year)
    if this_year >= today:
        return this_year
    return anniversary_for_year(original_date, today.year + 1)
```

#### Occurrence Count

Counts how many times the anniversary has occurred (including the original date):

```python
def anniversary_count(original_date: date, today: date) -> int:
    if original_date > today:
        return 0

    years_passed = today.year - original_date.year
    this_year = anniversary_for_year(original_date, today.year)

    if this_year > today:
        years_passed -= 1

    return max(1, years_passed + 1)
```

### 2.4 Special Event Calculations

Special events are either fixed-date holidays or calculated using algorithms.

#### Fixed Date Events

Simple month/day lookup for holidays like Christmas (December 25) or Halloween (October 31).

#### Gauss Easter Algorithm

Easter Sunday is calculated using the Gauss algorithm for the Gregorian calendar:

```python
def calculate_easter(year: int) -> date:
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451

    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1

    return date(year, month, day)
```

This algorithm:
- Works for any year in the Gregorian calendar
- Calculates Western (Catholic/Protestant) Easter
- Requires no external libraries or lunar data
- Is the foundation for all Easter-dependent holidays

#### Easter-Dependent Holidays

| Holiday | Calculation |
|---------|-------------|
| **Pentecost Sunday** | Easter + 49 days |

```python
def calculate_pentecost(year: int) -> date:
    easter = calculate_easter(year)
    return easter + timedelta(days=49)
```

#### Advent Calculation

Advent Sundays are calculated backwards from Christmas Eve:

```python
def calculate_advent(year: int, advent_num: int) -> date:
    christmas = date(year, 12, 24)

    days_back = (christmas.weekday() + 1) % 7
    if days_back == 0:
        days_back = 7

    advent_4 = christmas - timedelta(days=days_back)

    weeks_before_4th = 4 - advent_num
    return advent_4 - timedelta(days=weeks_before_4th * 7)
```

**Special case:** When Christmas Eve falls on a Sunday, it is NOT the 4th Advent - the algorithm correctly finds the previous Sunday.

### 2.5 DST (Daylight Saving Time) Calculations

DST events track timezone transitions for different regions. Two calculation patterns are used:

#### Nth Weekday of Month

For rules like "2nd Sunday in March" (USA summer time):

```python
def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> date:
    first_day = date(year, month, 1)
    first_weekday = first_day.weekday()

    days_until_first = (weekday - first_weekday) % 7
    first_occurrence = first_day + timedelta(days=days_until_first)

    return first_occurrence + timedelta(weeks=n - 1)
```

#### Last Weekday of Month

For rules like "last Sunday in October" (EU winter time):

```python
def last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    days_back = (last_day.weekday() - weekday) % 7
    return last_day - timedelta(days=days_back)
```

#### DST Region Rules

| Region | Summer Time | Winter Time |
|--------|-------------|-------------|
| **EU** | Last Sunday in March | Last Sunday in October |
| **USA** | 2nd Sunday in March | 1st Sunday in November |
| **Australia** | 1st Sunday in October | 1st Sunday in April |
| **New Zealand** | Last Sunday in September | 1st Sunday in April |

#### DST Active Detection

```python
def is_dst_active(region_info: dict, today: date) -> bool:
    last_summer = last_dst_event(region_info, "next_summer", today)
    last_winter = last_dst_event(region_info, "next_winter", today)
    return last_summer > last_winter
```

### 2.6 Custom Pattern Calculations

Custom Pattern events use `dateutil.rrule` (bundled in HA, no `manifest.json` entry needed) to generate occurrence dates from an RFC 5545-compatible rule.

Key functions in `calculations.py`:
- `next_custom_pattern(event_data, today) → date | None`
- `last_custom_pattern(event_data, today) → date | None`
- `occurrence_count_custom_pattern(event_data, today) → int`

The rule is **not** stored as an RRULE string — it is built at runtime from structured fields (`cp_freq`, `cp_interval`, `cp_dtstart`, `cp_day_rule`, `cp_bymonth`, ...). This makes editing individual parameters possible without RRULE parsing.

The anchor date (`cp_dtstart`) is always required. It is the `DTSTART` of the rrule, not necessarily the first occurrence.

EXDATE support: data model exists (`cp_exdates`), no UI in v1.

---

## 3. Entities

Each event creates multiple entities grouped under a common device.

### 3.1 Trip Entities

| Entity Type | Entity | Description |
|-------------|--------|-------------|
| **Sensor** | `days_until` | Days until trip starts (can be negative) |
| **Sensor** | `days_until_end` | Days until trip ends (can be negative) |
| **Sensor** | `event_date` | Start date (ISO 8601 timestamp) |
| **Sensor** | `trip_left_days` | Remaining days during active trip |
| **Sensor** | `trip_left_percent` | Remaining percentage (100→0) |
| **Sensor** | `url` *(optional)* | Event URL; only created when a URL is configured |
| **Sensor** | `memo` *(optional)* | Free-text notes; only created when a memo is configured |
| **Binary Sensor** | `trip_starts_today` | True on start day |
| **Binary Sensor** | `trip_active_today` | True during trip |
| **Binary Sensor** | `trip_ends_today` | True on end day |
| **Image** | `event_image` | Custom or default image |

> **Conditional sensors:** URL and Memo sensors are only created when the respective field is non-empty at setup time. After adding a URL/Memo via the Options Flow and reloading, the sensor is created automatically.

**Attributes on `event_date` sensor:**
- `event_name`, `event_type`, `end_date`, `trip_duration_days`
- `breakdown_years`, `breakdown_months`, `breakdown_weeks`, `breakdown_days`

### 3.2 Milestone Entities

| Entity Type | Entity | Description |
|-------------|--------|-------------|
| **Sensor** | `days_until` | Days until milestone (can be negative) |
| **Sensor** | `event_date` | Target date (ISO 8601 timestamp) |
| **Sensor** | `url` *(optional)* | Event URL; only created when a URL is configured |
| **Sensor** | `memo` *(optional)* | Free-text notes; only created when a memo is configured |
| **Binary Sensor** | `is_today` | True on the milestone day |
| **Image** | `event_image` | Custom or default image |

> **Conditional sensors:** See note in 3.1.

### 3.3 Anniversary Entities

| Entity Type | Entity | Description |
|-------------|--------|-------------|
| **Sensor** | `days_until_next` | Days until next occurrence |
| **Sensor** | `days_since_last` | Days since last occurrence |
| **Sensor** | `occurrences_count` | Total occurrences including original |
| **Sensor** | `next_date` | Next occurrence (ISO 8601 timestamp) |
| **Sensor** | `last_date` | Last occurrence (ISO 8601 timestamp) |
| **Sensor** | `url` *(optional)* | Event URL; only created when a URL is configured |
| **Sensor** | `memo` *(optional)* | Free-text notes; only created when a memo is configured |
| **Binary Sensor** | `is_today` | True on anniversary day |
| **Image** | `event_image` | Custom or default image |

> **Conditional sensors:** See note in 3.1.

### 3.4 Special Event Entities

Covers Traditional holidays, DST events, and Custom Pattern events.

| Entity Type | Entity | Description |
|-------------|--------|-------------|
| **Sensor** | `days_until` | Days until next occurrence |
| **Sensor** | `days_since_last` | Days since last occurrence |
| **Sensor** | `next_date` | Next occurrence (ISO 8601 timestamp) |
| **Sensor** | `last_date` | Last occurrence (ISO 8601 timestamp) |
| **Sensor** | `occurrence_count` | *(Custom Pattern only)* Total past occurrences |
| **Sensor** | `url` *(optional)* | Event URL; only created when a URL is configured |
| **Sensor** | `memo` *(optional)* | Free-text notes; only created when a memo is configured |
| **Binary Sensor** | `is_today` | True on event day |
| **Binary Sensor** | `is_dst_active` | *(DST events only)* True when DST active |
| **Image** | `event_image` | Custom or default image |

> **Conditional sensors:** See note in 3.1.

### 3.5 Image Entity System

Each event includes an image entity that displays either a custom image or a default SVG icon.

| Event Type | Default Icon | Color |
|------------|--------------|-------|
| Trip | Airplane | Blue |
| Milestone | Flag | Red |
| Anniversary | Heart | Pink |
| Special Event | Star | Purple |

**Image sources:**
1. **Uploaded file**: Stored as base64 in config entry data — no files on the server. Supported formats: JPEG, PNG, WebP, GIF. Maximum file size: 5 MB. Validation is done server-side in `_process_image_upload()`.
2. **Custom path**: `/local/images/my-event.jpg` (files placed in the `www/` directory of the HA config)
3. **Default SVG**: Auto-generated icon based on event type

**Attributes:**
- `image_type`: "user_defined" or "system_defined"
- `image_path`: File path, "base64_data", or "default_svg"

### 3.6 Calendar Entity

Created only for Calendar-type config entries (`CONF_ENTRY_TYPE = "calendar"`).

| Entity Type | Entity | Description |
|-------------|--------|-------------|
| **Calendar** | WhenHub Calendar | HA calendar showing scoped WhenHub events |

**State:**
- `on`: At least one WhenHub event is active today
- `off`: No active event today

The calendar iterates all loaded Event-type config entries whose `entry_id` matches the configured scope. Event representation per type:

| WhenHub Type | Calendar Event |
|---|---|
| Trip | Multi-day event (`start_date` .. `end_date`) |
| Milestone | Single-day event on `target_date` |
| Anniversary | Annual single-day event (incl. ordinal) |
| Special Event | Annual single-day event |
| Custom Pattern | All occurrences in the calendar view window |

---

## 4. ConfigFlow

### 4.1 Overview

WhenHub uses a menu-based ConfigFlow where users first select the event type, then configure event-specific parameters. All event types also support an OptionsFlow for reconfiguration after creation.

### 4.2 Flow Structure

```
async_step_user (menu)
│
├── trip           → [trip form] → create_entry
├── milestone      → [milestone form] → create_entry
├── anniversary    → [anniversary form] → create_entry
├── calendar       → [calendar scope] → [calendar_by_type | calendar_specific] → create_entry
└── special        → special_category →
    ├── traditional / calendar  → special_event → [image step] → create_entry
    ├── dst                     → dst_event → [image step] → create_entry
    └── custom_pattern          → cp_freq → cp_dtstart/interval →
            yearly:  cp_bymonth → cp_day_rule →
                       nth_weekday → cp_weekday_nth
                       last_weekday → cp_weekday_last
                       fixed_day → cp_fixed_day
            monthly: cp_day_rule → (same sub-steps as yearly)
            weekly:  cp_weekly (weekday checkboxes)
            daily:   (no sub-step)
        → cp_end → [cp_end_until | cp_end_count]
        → cp_image (URL, Memo, Image, notify_on_expiry if end set)
        → create_entry
```

### 4.3 Configuration Parameters

#### Trip

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes | Trip start |
| `end_date` | date | Yes | Trip end |
| `image_upload` | file | No | Upload image (JPEG/PNG/WebP/GIF, max 5 MB) |
| `image_path` | string | No | Path to image (e.g. `/local/images/trip.jpg`) |
| `url` | string | No | Website or booking URL |
| `memo` | string | No | Free-text notes (Markdown) |
| `notify_on_expiry` | boolean | No | Create Repairs issue when expired (default: false) |

#### Milestone

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target_date` | date | Yes | Target date |
| `image_upload` | file | No | Upload image (JPEG/PNG/WebP/GIF, max 5 MB) |
| `image_path` | string | No | Path to image |
| `url` | string | No | Website or related URL |
| `memo` | string | No | Free-text notes (Markdown) |
| `notify_on_expiry` | boolean | No | Create Repairs issue when expired (default: false) |

#### Anniversary

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target_date` | date | Yes | Original date (repeats yearly) |
| `image_upload` | file | No | Upload image |
| `image_path` | string | No | Path to image |
| `url` | string | No | Website or related URL |
| `memo` | string | No | Free-text notes (Markdown) |

*(No `notify_on_expiry` — anniversaries never expire)*

#### Special Event (Holiday / DST)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `special_category` | select | Yes | `traditional` / `calendar` / `dst` / `custom_pattern` |
| `special_type` | select | Cond | Specific holiday (traditional/calendar only) |
| `dst_type` | select | Cond | `next_change` / `next_summer` / `next_winter` (DST only) |
| `dst_region` | select | Cond | EU / USA / Australia / New Zealand (DST only) |
| `image_upload` | file | No | Upload image |
| `image_path` | string | No | Path to image |
| `url` | string | No | Website or related URL |
| `memo` | string | No | Free-text notes (Markdown) |

*(No `notify_on_expiry` — holidays and DST events are recurring)*

#### Custom Pattern

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `cp_freq` | select | Yes | `yearly` / `monthly` / `weekly` / `daily` |
| `cp_dtstart` | date | Yes | Anchor date — start of rule counting |
| `cp_interval` | int | Yes | Repeat every N periods (≥ 1) |
| `cp_day_rule` | select | Cond | `nth_weekday` / `last_weekday` / `fixed_day` (yearly + monthly only) |
| `cp_bymonth` | int | Cond | Month 1–12 (yearly only) |
| `cp_byday_pos` | int | Cond | 1–4 (nth_weekday only) |
| `cp_byday_weekday` | int | Cond | 0=Mo…6=So (nth/last weekday) |
| `cp_bymonthday` | int | Cond | 1–31 (fixed_day only) |
| `cp_byday_list` | list | Cond | Weekday indices (weekly only) |
| `cp_end_type` | select | Yes | `none` / `until` / `count` |
| `cp_until` | date | Cond | Last occurrence date (`end_type=until`) |
| `cp_count` | int | Cond | Total occurrences (`end_type=count`) |
| `image_upload` | file | No | Upload image |
| `image_path` | string | No | Path to image |
| `url` | string | No | URL |
| `memo` | string | No | Memo |
| `notify_on_expiry` | boolean | No | Only shown when `cp_end_type ≠ "none"` |

#### Calendar

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `calendar_scope` | select | Yes | `all` / `by_type` / `specific` |
| `calendar_types` | list | Cond | Event types to include (`scope=by_type`) |
| `calendar_event_ids` | list | Cond | Entry IDs to include (`scope=specific`) |

### 4.4 Options Flow

All event types can be reconfigured after creation:
1. Settings → Devices & Services → WhenHub
2. Click "Configure" on the desired event
3. Modify parameters and save

The Options Flow mirrors the Config Flow for each event type with pre-populated values. Converting between event types is not supported.

### 4.5 Expiry Repairs Fix Flow

When `notify_on_expiry` is enabled and an event expires, WhenHub creates a fixable issue in Home Assistant Repairs (Settings → System → Repairs).

**Expiry conditions per event type:**
- Trip: `end_date < today`
- Milestone: `target_date < today`
- Custom Pattern: `cp_end_type ≠ "none"` AND `next_custom_pattern()` returns `None`

The issue is created idempotently in every coordinator update cycle. It is deleted automatically when the event is no longer expired (e.g. after updating the dates via Options Flow).

**Fix flow (`repairs.py` / `WhenHubRepairsFlow`):**
1. User clicks "Fix" in HA Repairs
2. Confirmation form shown with `event_name` + `expiry_date`
3. Warning: check dashboards, automations, scripts before confirming
4. On confirm: `hass.config_entries.async_remove(entry_id)` — removes the entry

**Translations:**
- Issue title: `translations/{lang}.json` → `issues.expired_event.title`
- Fix flow form: `issues.expired_event.fix_flow.step.confirm`

---

## 5. Technical Reference

### 5.1 Project Language & Code Style

All development is done in **English** – code, comments, commit messages, issues, release notes, and documentation.

- **Language:** English for all variables, functions, comments, docstrings
- **Type Hints:** Used throughout
- **Docstrings:** Google-Style
- **Linting:** Ruff (E, F, W rules)
- **Line Length:** 120 characters

### 5.2 HACS Distribution

This integration is distributed via [HACS](https://hacs.xyz/). Requirements:

- **Repository structure:** `custom_components/whenhub/` with valid `manifest.json`
- **hacs.json:** Configuration file in repository root with `zip_release: true`
- **GitHub Releases:** Versions distributed via GitHub releases with ZIP asset
- **Validation:** `validate.yaml` workflow runs Hassfest and HACS validation on every push/PR

### 5.3 File Structure

```
WhenHub/
├── custom_components/
│   └── whenhub/
│       ├── __init__.py          # Integration setup (routes EVENT vs CALENDAR platforms)
│       ├── calendar.py          # FR08: CalendarEntity (WhenHubCalendar)
│       ├── config_flow.py       # ConfigFlow & OptionsFlow
│       ├── const.py             # Constants, sensor types, event definitions
│       ├── coordinator.py       # DataUpdateCoordinator (hourly)
│       ├── calculations.py      # Pure calculation functions (no HA dependencies)
│       ├── repairs.py           # FR13: Expiry fix flow (WhenHubRepairsFlow)
│       ├── sensor.py            # Sensor platform setup
│       ├── binary_sensor.py     # Binary sensor platform
│       ├── image.py             # Image entity platform
│       ├── sensors/
│       │   ├── base.py          # Base sensor classes
│       │   ├── trip.py          # Trip sensor implementation
│       │   ├── milestone.py     # Milestone sensor implementation
│       │   ├── anniversary.py   # Anniversary sensor implementation
│       │   ├── special.py       # Special event sensor implementation
│       │   ├── custom_pattern.py # FR09: Occurrence count sensor
│       │   └── url_memo.py      # FR11: URL and Memo sensors
│       └── translations/
│           ├── en.json          # English (fallback)
│           └── de.json          # German
├── tests/                       # Test suite (pytest + freezegun)
├── docs/                        # Internal documentation and plans
├── .github/
│   └── workflows/
│       ├── validate.yaml        # Hassfest & HACS validation
│       └── release.yml          # ZIP creation on release
└── <Project root>               # README, RELEASENOTES, LICENSE, hacs.json
```

### 5.4 Dependencies

| Feature | Implementation |
|---------|----------------|
| Easter calculation | Gauss algorithm in `calculations.py` |
| DST rules | Custom weekday calculations |
| Date parsing | Python `datetime` module |
| Custom Pattern | `dateutil.rrule` (bundled in HA — no `manifest.json` entry needed) |
| Image upload | `file_upload` HA dependency (declared in `manifest.json`) |

### 5.5 DataUpdateCoordinator

The integration uses Home Assistant's `DataUpdateCoordinator` for centralized data management.

**Update interval:** Once per hour (`UPDATE_INTERVAL = timedelta(hours=1)`)

Sensors will always show correct values since calculations use `date.today()` at the time of the update call. An hourly interval is sufficient for date-based countdown data.

At each update cycle, the coordinator also calls `_check_expiry_repair(today)` to maintain the Repairs issue state.

### 5.6 Entry Type Routing

`CONF_ENTRY_TYPE` in `entry.data` distinguishes between event entries and calendar entries:

| Entry Type | Platforms | Coordinator |
|------------|-----------|-------------|
| Event (default) | `SENSOR`, `IMAGE`, `BINARY_SENSOR` | `WhenHubCoordinator` per entry |
| `"calendar"` | `CALENDAR` | None (reads live from `hass.config_entries`) |

### 5.7 Device Registration

Each event creates a device that groups all its entities:

| Field | Value |
|-------|-------|
| **Name** | User-defined event name (entry title) |
| **Manufacturer** | "WhenHub" |
| **Model** | Dynamic based on event type (e.g., "Trip Tracker", "Anniversary Tracker") |
| **Identifier** | `entry_id` of the Config Entry |

### 5.8 Time Handling

All timestamp sensors use `device_class: timestamp` and store values in **UTC**. Home Assistant automatically converts these to the user's local timezone for display.

The integration respects Home Assistant's configured timezone for:
- Midnight/hourly update scheduling
- DST region auto-detection

### 5.9 Repairs Integration

WhenHub registers a repair fix flow via `repairs.py`. HA auto-discovers this file — no explicit registration in `__init__.py` needed.

The fix flow is triggered when the user clicks "Fix" on a WhenHub issue in the HA Repairs panel. Only expiry issues (`translation_key="expired_event"`) are currently implemented.

**Issue lifecycle:**
1. Coordinator update: `_check_expiry_repair(today)` called each cycle
2. If expired + `notify_on_expiry`: `async_create_issue(..., is_fixable=True)`
3. If not expired: `async_delete_issue(...)` — auto-resolves the issue
4. On entry unload: `async_delete_issue` cleanup in `async_unload_entry`

**Important import note:**
- `async_create_issue` / `async_delete_issue` / `IssueSeverity` → `homeassistant.helpers.issue_registry`
- `RepairsFlow` / `ConfirmRepairFlow` → `homeassistant.components.repairs`

### 5.10 Translations

WhenHub uses the Home Assistant translation system with `translation_key` at sensor level.

**Supported languages:**
- `en.json` - English (fallback)
- `de.json` - German

**Translated sections:**
- ConfigFlow dialogs (step titles, descriptions, field labels)
- Error messages
- Selector options (event types, DST regions, etc.)
- Entity names
- Issues (expiry notification title, fix flow confirmation)

> **Note:** `format_countdown_text()` outputs German ("5 Tage") regardless of HA language — this is intentional and not covered by the translation system.

### 5.11 manifest.json

| Field | Value | Explanation |
|-------|-------|-------------|
| `domain` | `whenhub` | Unique identifier |
| `config_flow` | `true` | UI configuration |
| `integration_type` | `device` | Creates device entries |
| `iot_class` | `calculated` | Data calculated locally |
| `dependencies` | `["file_upload"]` | Required for image uploads |
| `version` | `x.y.z` | Current version (single source of truth) |

---

## 6. Resources

### Home Assistant Development

| Topic | Link |
|-------|------|
| Developer Documentation | https://developers.home-assistant.io/ |
| Integration Manifest | https://developers.home-assistant.io/docs/creating_integration_manifest/ |
| ConfigFlow | https://developers.home-assistant.io/docs/config_entries_config_flow_handler/ |
| Sensor Entity | https://developers.home-assistant.io/docs/core/entity/sensor/ |
| Binary Sensor Entity | https://developers.home-assistant.io/docs/core/entity/binary-sensor/ |
| Image Entity | https://developers.home-assistant.io/docs/core/entity/image/ |
| Calendar Entity | https://developers.home-assistant.io/docs/core/entity/calendar/ |
| Internationalization | https://developers.home-assistant.io/docs/internationalization/core/ |
| DataUpdateCoordinator | https://developers.home-assistant.io/docs/integration_fetching_data/ |
| HA Repairs | https://developers.home-assistant.io/docs/repairs/ |

### Algorithm & Standard References

| Topic | Link |
|-------|------|
| Gauss Easter Algorithm | https://en.wikipedia.org/wiki/Date_of_Easter#Gauss's_Easter_algorithm |
| Daylight Saving Time | https://en.wikipedia.org/wiki/Daylight_saving_time_by_country |
| RFC 5545 iCalendar RRULE | https://www.rfc-editor.org/rfc/rfc5545 |
| dateutil rrule | https://dateutil.readthedocs.io/en/stable/rrule.html |

### Related Integrations

| Integration | Relevance |
|-------------|-----------|
| [Solstice Season](https://github.com/moerk-o/ha-solstice_season) | Astronomical season calculations (by same author) |
| [Sun (HA Core)](https://www.home-assistant.io/integrations/sun/) | Sunrise/sunset data |

---

## 7. Release Process

### Before Release

1. All changes merged into `main`
2. Bump version in `custom_components/whenhub/manifest.json`
3. Update `RELEASENOTES.md`:
   - Insert new content at top (without version heading — GitHub adds it)
   - Add version heading above previous release
   - Use consistent section headers:
     - ✨ New Features
     - 🐞 Bug Fixes
     - 🔧 Infrastructure
     - 📝 Documentation
     - 🗑️ Removed
4. Commit and push changes

### Create Release

```bash
gh release create vX.Y.Z --title "vX.Y.Z" --notes-file RELEASENOTES.md
```

### After Release

- GitHub workflow (`release.yml`) automatically creates `whenhub.zip` and attaches it to the release
- Verify ZIP is present in release assets

---

## 8. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12 | Initial implementation with Trip, Milestone, Anniversary |
| 2.0.0 | 2025-01 | Internationalization (DE/EN), timestamp device_class, relative time display |
| 2.2.1 | 2025-02 | Special Events (holidays, DST), OptionsFlow fixes, removed astronomical events |
| 2.3.0 | 2026-03 | FR08 Calendar entity, FR09 Custom Pattern, FR11 URL/Memo sensors, Bug 003 fixes |
| 2.4.0 | 2026-05 | FR13 Expiry notifications via HA Repairs |
| 2.4.1 | 2026-05 | Fix #12: Image upload validation (extension check, 5 MB size limit), options flow error translations |
| 3.0.0 | 2026-05 | FR13 Expiry notifications (HA Repairs), Fix #12 image validation, Fix #14 entity ID standardization (English type keys, automatic migration v1→v2) |

For detailed release notes with descriptions and issue links, see [`RELEASENOTES.md`](RELEASENOTES.md).

---

*This technical reference serves as the complete specification and documentation of the `whenhub` Home Assistant integration.*
