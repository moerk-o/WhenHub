# Technical Reference: Home Assistant Integration `whenhub`

**Version:** 2.2.1
**Date:** February 6, 2026
**Target Platform:** Home Assistant Custom Integration
**Development Language:** English (code, comments, variables)
**Translations:** English (fallback), German
**Repository:** https://github.com/moerk-o/WhenHub

---

## 1. Project Overview

### 1.1 Purpose

**The origin story:** The kids kept asking "How much longer until vacation?" or "How many days until my birthday?". WhenHub was created to answer these questions by displaying countdown information on Home Assistant dashboards - showing an image of the event with the remaining days prominently displayed.

WhenHub provides:

- Multiple event types for different use cases (trips, milestones, anniversaries, holidays)
- Countdown sensors with days until/since calculations
- Binary sensors for "is today" detection
- Image entities for visual event representation
- Breakdown attributes for localized countdown text (years, months, weeks, days)
- Full UI configuration via ConfigFlow

### 1.2 Event Types Overview

| Event Type | Use Case | Key Feature |
|------------|----------|-------------|
| **Trip** | Multi-day events (vacations, visits) | Start/End dates, progress tracking |
| **Milestone** | One-time important dates | Single target date, can be in the past |
| **Anniversary** | Yearly recurring events (birthdays) | Leap year handling, occurrence counting |
| **Special Event** | Predefined holidays | Gauss Easter algorithm, DST rules |

### 1.3 Naming Convention

- **Domain:** `whenhub`
- **Entity Prefix:** User-defined event name (e.g., "Denmark Vacation" → `sensor.denmark_vacation_*`)
- **Unique ID Pattern:** `{entry_id}_{sensor_type}`

---

## 2. Calculation Logic

All calculations are implemented in pure Python without external dependencies. The `calculations.py` module contains deterministic functions that take explicit date parameters for testability.

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
    # Christmas Eve
    christmas = date(year, 12, 24)

    # Find the Sunday before Christmas Eve
    days_back = (christmas.weekday() + 1) % 7
    if days_back == 0:
        days_back = 7

    # 4th Advent is the last Sunday before Christmas Eve
    advent_4 = christmas - timedelta(days=days_back)

    # Calculate requested Advent (1, 2, 3, or 4)
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

    # Days until the first desired weekday
    days_until_first = (weekday - first_weekday) % 7
    first_occurrence = first_day + timedelta(days=days_until_first)

    # nth occurrence (n-1 weeks after the first)
    return first_occurrence + timedelta(weeks=n - 1)
```

#### Last Weekday of Month

For rules like "last Sunday in October" (EU winter time):

```python
def last_weekday_of_month(year: int, month: int, weekday: int) -> date:
    # Last day of the month
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    # Days back to the desired weekday
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

Determines whether summer time (DST) or winter time (standard) is currently active:

```python
def is_dst_active(region_info: dict, today: date) -> bool:
    last_summer = last_dst_event(region_info, "next_summer", today)
    last_winter = last_dst_event(region_info, "next_winter", today)

    # The more recent transition determines the current state
    return last_summer > last_winter
```

**Example (EU):**
- January 15: `is_dst_active` = False (winter time, last transition was October)
- July 15: `is_dst_active` = True (summer time, last transition was March)

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
| **Binary Sensor** | `trip_starts_today` | True on start day |
| **Binary Sensor** | `trip_active_today` | True during trip |
| **Binary Sensor** | `trip_ends_today` | True on end day |
| **Image** | `event_image` | Custom or default image |

**Attributes on `event_date` sensor:**
- `event_name`, `event_type`, `end_date`, `trip_duration_days`
- `breakdown_years`, `breakdown_months`, `breakdown_weeks`, `breakdown_days`

### 3.2 Milestone Entities

| Entity Type | Entity | Description |
|-------------|--------|-------------|
| **Sensor** | `days_until` | Days until milestone (can be negative) |
| **Sensor** | `event_date` | Target date (ISO 8601 timestamp) |
| **Binary Sensor** | `is_today` | True on the milestone day |
| **Image** | `event_image` | Custom or default image |

### 3.3 Anniversary Entities

| Entity Type | Entity | Description |
|-------------|--------|-------------|
| **Sensor** | `days_until_next` | Days until next occurrence |
| **Sensor** | `days_since_last` | Days since last occurrence |
| **Sensor** | `event_date` | Next anniversary (ISO 8601 timestamp) |
| **Sensor** | `occurrences_count` | Total occurrences including original |
| **Sensor** | `next_date` | Next occurrence (ISO 8601 timestamp) |
| **Sensor** | `last_date` | Last occurrence (ISO 8601 timestamp) |
| **Binary Sensor** | `is_today` | True on anniversary day |
| **Image** | `event_image` | Custom or default image |

**Attributes on `event_date` sensor:**
- `event_name`, `event_type`, `initial_date`, `years_on_next`
- `breakdown_years`, `breakdown_months`, `breakdown_weeks`, `breakdown_days`

### 3.4 Special Event Entities

| Entity Type | Entity | Description |
|-------------|--------|-------------|
| **Sensor** | `days_until` | Days until next occurrence |
| **Sensor** | `days_since_last` | Days since last occurrence |
| **Sensor** | `event_date` | Next occurrence (ISO 8601 timestamp) |
| **Sensor** | `next_date` | Next occurrence (ISO 8601 timestamp) |
| **Sensor** | `last_date` | Last occurrence (ISO 8601 timestamp) |
| **Binary Sensor** | `is_today` | True on event day |
| **Binary Sensor** | `is_dst_active` | True when DST active (DST events only) |
| **Image** | `event_image` | Custom or default image |

### 3.5 Image Entity System

Each event includes an image entity that displays either a custom image or a default SVG icon.

| Event Type | Default Icon | Color |
|------------|--------------|-------|
| Trip | Airplane | Blue |
| Milestone | Flag | Red |
| Anniversary | Heart | Pink |
| Special Event | Star | Purple |

**Image sources:**
1. **Custom path**: `/local/images/my-event.jpg`
2. **Base64 data**: Directly embedded image data
3. **Default SVG**: Auto-generated icon based on event type

**Attributes:**
- `image_type`: "user_defined" or "system_defined"
- `image_path`: File path, "base64_data", or "default_svg"

---

## 4. ConfigFlow

### 4.1 Overview

WhenHub uses a menu-based ConfigFlow where users first select the event type, then configure event-specific parameters.

### 4.2 Flow Structure

```
┌─────────────────────────────────────┐
│         async_step_user             │
│         (Menu Selection)            │
│                                     │
│  ○ Trip                             │
│  ○ Milestone                        │
│  ○ Anniversary                      │
│  ○ Special Event                    │
└─────────────────────────────────────┘
                 │
       ┌─────────┼─────────┬──────────┐
       ▼         ▼         ▼          ▼
   ┌───────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
   │ Trip  │ │Milestone│ │Annivers.│ │ Special │
   │ Form  │ │  Form   │ │  Form   │ │  Menu   │
   └───────┘ └─────────┘ └─────────┘ └────┬────┘
       │         │           │            │
       │         │           │       ┌────┴────┐
       │         │           │       ▼         ▼
       │         │           │  ┌────────┐ ┌───────┐
       │         │           │  │Holiday │ │  DST  │
       │         │           │  │  Form  │ │ Form  │
       │         │           │  └────────┘ └───────┘
       │         │           │       │         │
       └─────────┴───────────┴───────┴─────────┘
                             │
                             ▼
              ┌─────────────────────────────────┐
              │       async_create_entry        │
              │                                 │
              │  - Set Unique ID                │
              │  - Create Config Entry          │
              │  - Start Integration Setup      │
              └─────────────────────────────────┘
```

### 4.3 Configuration Parameters

#### Trip

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_name` | string | Yes | Display name |
| `start_date` | date | Yes | Trip start (DateSelector) |
| `end_date` | date | Yes | Trip end (DateSelector) |
| `image_path` | string | No | Custom image path |

#### Milestone

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_name` | string | Yes | Display name |
| `target_date` | date | Yes | Target date (DateSelector) |
| `image_path` | string | No | Custom image path |

#### Anniversary

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_name` | string | Yes | Display name |
| `target_date` | date | Yes | Original date (DateSelector) |
| `image_path` | string | No | Custom image path |

#### Special Event (Holiday)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_name` | string | Yes | Display name |
| `special_category` | select | Yes | Category (Traditional/Calendar/DST) |
| `special_type` | select | Yes | Specific holiday |
| `image_path` | string | No | Custom image path |

#### Special Event (DST)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event_name` | string | Yes | Display name |
| `dst_type` | select | Yes | next_change/next_summer/next_winter |
| `dst_region` | select | Yes | EU/USA/Australia/New Zealand |
| `image_path` | string | No | Custom image path |

### 4.4 Options Flow

All events can be reconfigured after creation:
1. Settings → Devices & Services → WhenHub
2. Click "Configure" on the desired event
3. Modify parameters and save

**Limitation:** Converting between event types is not supported.

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
- **Validation:** `validate.yaml` workflow runs Hassfest and HACS validation

### 5.3 File Structure

```
WhenHub/
├── custom_components/
│   └── whenhub/
│       ├── __init__.py          # Integration setup
│       ├── config_flow.py       # ConfigFlow & OptionsFlow
│       ├── const.py             # Constants, sensor types, event definitions
│       ├── coordinator.py       # DataUpdateCoordinator
│       ├── calculations.py      # Pure calculation functions
│       ├── sensor.py            # Sensor platform setup
│       ├── binary_sensor.py     # Binary sensor platform
│       ├── image.py             # Image entity platform
│       ├── sensors/
│       │   ├── base.py          # Base sensor classes
│       │   ├── trip.py          # Trip sensor implementation
│       │   ├── milestone.py     # Milestone sensor implementation
│       │   ├── anniversary.py   # Anniversary sensor implementation
│       │   └── special.py       # Special event sensor implementation
│       └── translations/
│           ├── en.json          # English (fallback)
│           └── de.json          # German
├── tests/                       # Test suite
├── .github/
│   └── workflows/
│       ├── validate.yaml        # Hassfest & HACS validation
│       └── release.yml          # ZIP creation on release
└── <Project root>               # README, LICENSE, hacs.json
```

### 5.4 Dependencies

WhenHub has **no external Python dependencies**. All calculations are implemented in pure Python:

| Feature | Implementation |
|---------|----------------|
| Easter calculation | Gauss algorithm in `calculations.py` |
| DST rules | Custom weekday calculations |
| Date parsing | Python `datetime` module |

This is intentional - fewer dependencies mean easier installation and fewer potential conflicts.

### 5.5 DataUpdateCoordinator

The integration uses Home Assistant's `DataUpdateCoordinator` for centralized data management.

**Update Schedule:** Once per day at midnight (local time)

The coordinator recalculates all date-based values at midnight to ensure sensors reflect the new day accurately.

### 5.6 Device Registration

Each event creates a device that groups all its entities:

| Field | Value |
|-------|-------|
| **Name** | User-defined event name |
| **Manufacturer** | "WhenHub" |
| **Model** | Dynamic based on event type (e.g., "Trip Tracker", "Anniversary Tracker") |
| **Identifier** | `entry_id` of the Config Entry |

### 5.7 Time Handling

All timestamp sensors use `device_class: timestamp` and store values in **UTC**. Home Assistant automatically converts these to the user's local timezone for display.

The integration respects Home Assistant's configured timezone for:
- Midnight update scheduling
- DST region auto-detection

### 5.8 Translations

WhenHub uses the Home Assistant translation system with `translation_key` at sensor level.

**Supported languages:**
- `en.json` - English (fallback)
- `de.json` - German

**Translated sections:**
- ConfigFlow dialogs (step titles, descriptions, field labels)
- Error messages
- Selector options (event types, DST regions)
- Entity names

### 5.9 manifest.json

| Field | Value | Explanation |
|-------|-------|-------------|
| `domain` | `whenhub` | Unique identifier |
| `config_flow` | `true` | UI configuration |
| `integration_type` | `device` | Creates device entries |
| `iot_class` | `calculated` | Data calculated locally |
| `requirements` | `[]` | No external dependencies |
| `version` | `x.y.z` | Current version |

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
| Internationalization | https://developers.home-assistant.io/docs/internationalization/core/ |
| DataUpdateCoordinator | https://developers.home-assistant.io/docs/integration_fetching_data/ |

### Algorithm References

| Topic | Link |
|-------|------|
| Gauss Easter Algorithm | https://en.wikipedia.org/wiki/Date_of_Easter#Gauss's_Easter_algorithm |
| Daylight Saving Time | https://en.wikipedia.org/wiki/Daylight_saving_time_by_country |

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
   - Insert new content at top (without version heading - GitHub adds it)
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

For detailed release notes with descriptions and issue links, see [`RELEASENOTES.md`](RELEASENOTES.md).

---

*This technical reference serves as the complete specification and documentation of the `whenhub` Home Assistant integration.*
