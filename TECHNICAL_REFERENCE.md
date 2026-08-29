# Technical Reference: Home Assistant Integration `whenhub`

**Version:** 3.3.1
**Date:** August 2026
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
- Services to create, update and delete events from automations and scripts

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

#### Timezone Auto-Detection

When a DST event is first created, the region selector is pre-populated based on `hass.config.time_zone`:

```python
TIMEZONE_TO_REGION = {
    "Europe/": "eu",           # prefix match
    "America/New_York": "usa",
    "America/Chicago": "usa",
    "America/Denver": "usa",
    "America/Los_Angeles": "usa",
    "America/Toronto": "usa",
    "Australia/": "australia", # prefix match
    "Pacific/Auckland": "new_zealand",
}
```

If no match is found, the region selector has no pre-selection and the user must choose manually. Users may always select any region regardless of their actual timezone (e.g. expats tracking their home country's DST).

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
- `start_date_source_entity` *(only present when start date comes from a HA entity)*
- `end_date_source_entity` *(only present when end date comes from a HA entity)*

**Icon:** `mdi:calendar-sync` when start or end date is sourced from a HA entity; `mdi:calendar` otherwise.

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

**Attributes on `event_date` sensor:**
- `event_name`, `event_type`
- `breakdown_years`, `breakdown_months`, `breakdown_weeks`, `breakdown_days`
- `date_source_entity` *(only present when date comes from a HA entity)*

**Icon:** `mdi:calendar-sync` when date is sourced from a HA entity; `mdi:calendar` otherwise.

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

**Attributes on `event_date` sensor:**
- `event_name`, `event_type`, `initial_date`, `years_on_next`
- `breakdown_years`, `breakdown_months`, `breakdown_weeks`, `breakdown_days`
- `date_source_entity` *(only present when date comes from a HA entity)*

**Icon:** `mdi:calendar-sync` when date is sourced from a HA entity; `mdi:calendar` otherwise.

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

**State and `image_last_updated`:**

`ImageEntity.state` is `@final` in HA Core and returns `image_last_updated.isoformat()`
(or `None` if that value is unset). `WhenHubImage` therefore does not define `state` of
its own; it sets `_attr_image_last_updated` to `dt_util.utcnow()` in `__init__`. The
frontend appends the state to the image URL, so this value is the cache key of the served
image.

Since the entity is recreated on every config entry reload, an image changed through the
options flow gets a new timestamp for free — no extra invalidation logic is needed. A
Home Assistant restart also renews the timestamp, which is harmless (an unchanged image is
simply re-fetched once).

`content_type` follows the same pattern: it is a `cached_property` backed by
`_attr_content_type` in Core, and `WhenHubImage` computes the value once in `__init__`
(`_detect_content_type()`) rather than overriding the property. All inputs
(`image_data`, `image_mime`, `image_path`) are fixed for the lifetime of the entity.

> Prior to 3.3.1 the entity overrode `state` with the fixed string `"idle"` and never set
> `image_last_updated` (#23).

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
| `start_date` | date | Cond | Trip start; required when `start_date_use_entity=false` |
| `start_date_use_entity` | boolean | No | Use a HA entity as start date source |
| `start_date_entity_id` | entity | Cond | Source entity (`device_class: date` or `timestamp`); required when `start_date_use_entity=true` |
| `end_date` | date | Cond | Trip end; required when `end_date_use_entity=false` |
| `end_date_use_entity` | boolean | No | Use a HA entity as end date source |
| `end_date_entity_id` | entity | Cond | Source entity; required when `end_date_use_entity=true` |
| `image_upload` | file | No | Upload image (JPEG/PNG/WebP/GIF, max 5 MB) |
| `image_path` | string | No | Path to image (e.g. `/local/images/trip.jpg`) |
| `url` | string | No | Website or booking URL |
| `memo` | string | No | Free-text notes (Markdown) |
| `notify_on_expiry` | boolean | No | Create Repairs issue when expired (default: false) |

#### Milestone

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target_date` | date | Cond | Target date; required when `event_date_use_entity=false` |
| `event_date_use_entity` | boolean | No | Use a HA entity as date source |
| `event_date_entity_id` | entity | Cond | Source entity (`device_class: date` or `timestamp`); required when `event_date_use_entity=true` |
| `image_upload` | file | No | Upload image (JPEG/PNG/WebP/GIF, max 5 MB) |
| `image_path` | string | No | Path to image |
| `url` | string | No | Website or related URL |
| `memo` | string | No | Free-text notes (Markdown) |
| `notify_on_expiry` | boolean | No | Create Repairs issue when expired (default: false) |

#### Anniversary

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target_date` | date | Cond | Original date (repeats yearly); required when `event_date_use_entity=false` |
| `event_date_use_entity` | boolean | No | Use a HA entity as date source |
| `event_date_entity_id` | entity | Cond | Source entity (`device_class: date` or `timestamp`); required when `event_date_use_entity=true` |
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

## 5. Services

Three services (FR15) expose what the Config and Options Flow do, so events can be
managed from automations and scripts: `create_event`, `update_event`, `delete_event`.
Custom Pattern creation and pattern fields are out of scope (see issue #25); Calendar
entries are rejected by all three.

### 5.1 Registration

`services.py` defines the schemas and handlers, `async_setup_services(hass)` registers
them. It is called from `async_setup()` in `__init__.py`, not from `async_setup_entry()`
— services are global and must exist exactly once, no matter how many events are
configured.

```python
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    async_setup_services(hass)
    return True
```

Consequence: on an installation without a single config entry the integration is never
loaded, so the services do not exist yet. One event or calendar is enough.

`CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)` documents that `whenhub:`
in `configuration.yaml` is not a supported way to configure the integration.

All three services use `SupportsResponse.OPTIONAL` (see the ADR in 5.6).

### 5.2 Addressing via `device_id`

`update_event` and `delete_event` take a `device_id`. Every WhenHub event is one device
(`identifiers={(DOMAIN, entry.entry_id)}`, see 6.7), so the UI shows a device picker and
an automation can reach the event from any of its entities.

`_resolve_entry()` walks `device.config_entries`, takes the first entry belonging to
`whenhub` and rejects three cases with a `ServiceValidationError`:

| Situation | translation_key |
|---|---|
| No device with that ID | `device_not_found` |
| Device belongs to another integration | `device_not_whenhub` |
| Device is a WhenHub Calendar entry | `calendar_not_supported` |

### 5.3 Field validation

The service vocabulary differs from the stored data in two places, and `services.py`
translates between them:

| Service parameter | Config entry keys |
|---|---|
| `event_type: dst` | `event_type: special` + `special_category: dst` |
| `target_date_entity` | `event_date_use_entity` + `event_date_entity_id` |
| `start_date_entity` | `start_date_use_entity` + `start_date_entity_id` |
| `end_date_entity` | `end_date_use_entity` + `end_date_entity_id` |

`_service_event_type()` computes the reverse for an existing entry and returns `dst` and
`custom_pattern` as types of their own, which is what the responses report and what the
field check works on.

`_TYPE_FIELDS` maps each service event type to the type-specific parameters it accepts.
Any other type-specific parameter in the call is rejected with `field_not_allowed` — a
`target_date` on a trip is an error, not a silently ignored field. Generic parameters
(`image_path`, `url`, `memo`) are accepted everywhere.

`notify_on_expiry` follows the rules of the Options Flow: trips and milestones always,
Custom Patterns only when `cp_end_type != "none"`, everything else is rejected with
`notify_not_supported`. Only `true` is rejected — `notify_on_expiry: false` is accepted
for every type as a no-op, so a generic script can always send the parameter.

Dates are normalized with `date.fromisoformat(value).isoformat()`. Normalizing matters:
Python also accepts `20260712`, while the trip date order is compared as a string and
the stored value is read back by the calendar entity and the Options Flow.

An entity used as a date source must exist and carry device class `date` or `timestamp`
— the same filter the entity picker in the Config Flow applies.

When a date field is created from an entity source, the fixed date key is still written
with today's date as a placeholder. The calendar entity reads `data[CONF_START_DATE]`
and `data[CONF_TARGET_DATE]` directly, and the Options Flow pre-fills the field when the
entity source is switched off again.

### 5.4 Import flow for creation

`create_event` does not build a `ConfigEntry`; it starts a config flow:

```python
result = await hass.config_entries.flow.async_init(
    DOMAIN, context={"source": SOURCE_IMPORT}, data=entry_data
)
```

`ConfigFlow.async_step_import()` receives the finished entry data plus the control keys
`name` and `auto_rename`, applies the trip date check and the name check, and creates the
entry. It aborts with `invalid_dates` or `name_exists`; `services.py` turns the abort
reason into a `ServiceValidationError` carrying the same key.

Two helpers are shared by the flows and the services so all paths accept exactly the same
input:

| Helper (in `config_flow.py`) | Used by |
|---|---|
| `validate_trip_date_order(start, end)` | `async_step_trip`, `async_step_trip_options`, `async_step_import`, `update_event` |
| `existing_event_names(hass, ignore_entry_id=None)` | `_suggest_event_name()`, the rename check in `update_event` |

### 5.5 Update and delete

**Update.** `_apply_date_field()` builds the new entry data and the `changed` map at the
same time, field by field. `changed` reports the *effective* value: while a date comes
from an entity, its fixed-date key reads as `null`, which is why switching a source
produces two entries in `changed`. When `changed` is empty nothing is written at all, and
the response is `changed: {}`.

If something changed, the entry is written and then reloaded explicitly:

```python
with suppress_update_reload(hass, entry.entry_id):
    hass.config_entries.async_update_entry(entry, data=new_data, title=title)
    await hass.config_entries.async_reload(entry.entry_id)
```

The explicit reload is what makes a `blocking: true` call deterministic: when the service
returns, the entities already carry the new values. `async_update_entry()` also fires the
update listener registered in `async_setup_entry()`, which reloads as well —
`suppress_update_reload()` (see 6.13) turns that reload off for the duration of the block,
so one update costs exactly one reload.

**Delete.** The entity list is read from the entity registry *before*
`hass.config_entries.async_remove()`, because `async_unload_entry()` removes the
entities from the registry — read afterwards, `removed_entities` would always be empty.
Unloading deletes an open `expired_<entry_id>` Repairs issue; `async_remove_entry()`
deletes every remaining issue of the entry (see 6.9).

### 5.6 Design decisions

#### Name collision is an error, not silent numbering

**Decision:** `create_event` rejects a name that already exists. `auto_rename: true`
switches to the numbering the Config Flow uses ("Denmark 2", "Denmark 3"). `update_event`
rejects a rename onto an existing name and has no `auto_rename` — renaming to the
unchanged current name is a no-op, not an error.

**Context:** `_suggest_event_name()` numbers up silently, which is right for the UI:
a human sees the suggested name and clicks. A service call has no such moment.

**Why this approach:** A faulty automation that fires nightly would otherwise create
"Denmark 2" … "Denmark 74" without anyone noticing. Failing loudly turns that into a
visible error in the automation trace on the first night. Bulk creation still works — it
just has to ask for the numbering. On `update_event` the same rule keeps device names
unique, which matters because `device_id` is how the other two services pick their
target and a device picker with two identical names is unusable.

**Alternatives considered:**
- Always number up, as in the Config Flow — rejected, see above.
- Reject and offer no way to number — rejected: bulk creation from a list of names is
  one of the reasons the services exist.

**Consequences:** Automations that create events need to handle the error or pass
`auto_rename`. Names stay unique across all entries, which the rename check relies on.

#### One reload per update_event

**Decision:** `update_event` keeps its explicit `async_reload()` and suppresses the reload
of the update listener for the duration of that call, via the `suppress_update_reload()`
context manager in `__init__.py`. The listener itself, the options flow and the entity
rename auto-migration are unchanged.

**Context:** `async_update_entry()` fires every update listener of the entry, and the
listener registered in `async_setup_entry()` reloads. `update_event` also reloaded
explicitly so that a `blocking: true` call returns only once the entities carry the new
values — two reloads per call (#29). Home Assistant starts the listener task eagerly, so
its reload is already under way before the service continues; the service cannot simply
wait for it, because it holds no handle to that task.

**Why this approach:** The listener is the reload path for *every* writer of the entry —
not just the options flow, but also the entity rename auto-migration in
`_setup_entity_registry_listener()` (#19), which relies on it to get the coordinator onto
the renamed entity. Suppressing it for exactly one caller leaves that path intact and
keeps the change local to the one place that reloads itself. The suppression is
deterministic: the eagerly started listener runs inside the `with` block, and even without
eager start it would run at the first suspension point, which is the caller's own
`async_reload()` inside the block.

**Alternatives considered:**
- Drop the explicit reload in the service and let the listener do it — rejected: the
  service would return while the listener's reload is still running, so a `blocking: true`
  call would no longer guarantee that the entities show the new values.
- Remove the update listener and reload from the options flow instead — rejected: it
  changes the options flow, has to be repeated in every `_finalize_options()` path, and
  breaks the rename auto-migration, which updates the entry without going through a flow.

**Consequences:** A caller that updates an entry and reloads it itself has to use
`suppress_update_reload()`, otherwise the entry is reloaded twice again. Anyone writing
the entry without reloading keeps the listener's reload for free, unchanged.

#### Fixed date does not silently replace an entity source

**Decision:** Passing a fixed date for a field that currently reads from an entity is
rejected with `date_source_active`. `replace_date_source: true` detaches the entity and
stores the date. The opposite direction — pointing a field at an entity while it holds a
fixed date — needs no parameter.

**Context:** Since #9 a date can come from an entity. Both ways of setting it are
plausible in an automation, but only one of them destroys configuration.

**Why this approach:** Overwriting the source would silently break the link a user set up
deliberately, and the sensor would keep working, so nobody notices. The asymmetry follows
the loss: switching to an entity leaves the fixed date stored and is reversible, dropping
the entity id is not.

**Alternatives considered:**
- Always allow it — rejected: silent loss of configuration.
- Always refuse it — rejected: a batch run that puts a whole set of events onto fixed
  dates is a legitimate use case, and there would be no way to do it.

**Consequences:** One extra parameter in `update_event`, and automations that switch
sources have to say so explicitly.

#### `SupportsResponse.OPTIONAL` for all three services

**Decision:** All three services return a response only when the caller asks for it with
`response_variable`.

**Context:** Home Assistant offers `NONE`, `OPTIONAL` and `ONLY`. The responses are
useful — the created `device_id`, the fields that actually changed, the entities that
were removed — but most calls will not read them.

**Why this approach:** With `ONLY` a call without `response_variable` fails, which would
break the most common uses: a dashboard button, a script action, a scene. `OPTIONAL`
costs nothing when the response is discarded and keeps it available for automations that
chain calls, for example creating an event and remembering its `device_id`.

**Alternatives considered:**
- `NONE` — rejected: `create_event` would give no way to learn the `device_id` of the
  event it just made, which makes it hard to chain with `update_event`.
- `ONLY` — rejected: fails in exactly the simple cases these services are for.

**Consequences:** Handlers always build the response even when it is thrown away. That is
a dict per call, negligible next to a config entry reload.

#### Creation through the config flow import step

**Decision:** `create_event` creates the entry with
`hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_IMPORT}, data=…)`
and a new `async_step_import()`, instead of building a `ConfigEntry` object.

**Context:** A config entry can be added directly through the internal API. The Config
Flow already contains the validation, name suggestion and entry creation for exactly this
data.

**Why this approach:** The import source is the documented way to create entries
programmatically, and Home Assistant handles unique id, entry version, setup and the
`async_migrate_entry` path for free. It also keeps the service honest: the same code
decides whether a name is free and whether a trip's dates are in order, so a service call
cannot produce an entry the UI would reject.

**Alternatives considered:**
- Build the `ConfigEntry` directly and hand it to `hass.config_entries.async_add()` —
  rejected: bypasses the flow, duplicates the validation, and version and migration
  handling would have to be maintained twice.
- Validate in `services.py` and let the import step only create — rejected: the trip
  date check would then exist in two places, and the abort/error mapping got no simpler.

**Consequences:** The service has to interpret flow results: `FlowResultType.ABORT`
becomes a `ServiceValidationError` whose key equals the abort reason, so an abort reason
and an exception key have to stay in sync (`invalid_dates`, `name_exists` exist in both
`config.abort` and `exceptions`).

### 5.7 Errors and translations

Every rejection is a `ServiceValidationError` with `translation_domain=DOMAIN` and a
`translation_key` from the `exceptions` block of the translation files, so Home Assistant
shows a translated message in the automation trace and the UI.

`services.yaml` describes the parameters for the UI; the names and descriptions live in
`translations/en.json` and `translations/de.json` under `services.*`. hassfest validates
that every service and every field in `services.yaml` has a translation — both have to be
changed together.

Date parameters use a `text` selector rather than a `date` selector on purpose: entering
a distant date as an ISO string instead of scrolling through a date picker is one of the
reasons for these services (issue #10).

---

## 6. Technical Reference

### 6.1 Project Language & Code Style

All development is done in **English** – code, comments, commit messages, issues, release notes, and documentation.

- **Language:** English for all variables, functions, comments, docstrings
- **Type Hints:** Used throughout
- **Docstrings:** Google-Style
- **Linting:** Ruff (E, F, W rules)
- **Line Length:** 120 characters

### 6.2 HACS Distribution

This integration is distributed via [HACS](https://hacs.xyz/). Requirements:

- **Repository structure:** `custom_components/whenhub/` with valid `manifest.json`
- **hacs.json:** Configuration file in repository root with `zip_release: true`
- **GitHub Releases:** Versions distributed via GitHub releases with ZIP asset
- **Validation:** `validate.yaml` workflow runs Hassfest and HACS validation on every push/PR

### 6.3 File Structure

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
│       ├── services.py          # FR15: create_event / update_event / delete_event
│       ├── services.yaml        # FR15: Service parameters for the UI
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

### 6.4 Dependencies

| Feature | Implementation |
|---------|----------------|
| Easter calculation | Gauss algorithm in `calculations.py` |
| DST rules | Custom weekday calculations |
| Date parsing | Python `datetime` module |
| Custom Pattern | `dateutil.rrule` (bundled in HA — no `manifest.json` entry needed) |
| Image upload | `file_upload` HA dependency (declared in `manifest.json`) |

### 6.5 DataUpdateCoordinator

The integration uses Home Assistant's `DataUpdateCoordinator` for centralized data management.

**Update interval:** Once per hour (`UPDATE_INTERVAL = timedelta(hours=1)`)

Sensors will always show correct values since calculations use `date.today()` at the time of the update call. An hourly interval is sufficient for date-based countdown data.

At each update cycle, the coordinator also calls `_check_expiry_repair(today)` to maintain the Repairs issue state.

**Entity date source resolution:** When a date field is configured to use a HA entity, the coordinator calls `_resolve_date(entity_id, field_name)` instead of reading the static config value. This method:
1. Reads `hass.states.get(entity_id)` — returns `None` if the entity doesn't exist
2. Rejects states `"unavailable"` or `"unknown"` with `UpdateFailed`
3. Delegates to `_parse_entity_date(state)` which handles:
   - `device_class: date` → parses `YYYY-MM-DD` state string
   - `device_class: timestamp` → parses ISO-8601 UTC timestamp, converts to local date
4. Raises `UpdateFailed` on any parse error

Trip entries may have entity sources on start date, end date, or both independently.

### 6.6 Entry Type Routing

`CONF_ENTRY_TYPE` in `entry.data` distinguishes between event entries and calendar entries:

| Entry Type | Platforms | Coordinator |
|------------|-----------|-------------|
| Event (default) | `SENSOR`, `IMAGE`, `BINARY_SENSOR` | `WhenHubCoordinator` per entry |
| `"calendar"` | `CALENDAR` | None (reads live from `hass.config_entries`) |

### 6.7 Device Registration

Each event creates a device that groups all its entities:

| Field | Value |
|-------|-------|
| **Name** | User-defined event name (entry title) |
| **Manufacturer** | "WhenHub" |
| **Model** | Dynamic based on event type (e.g., "Trip Tracker", "Anniversary Tracker") |
| **Identifier** | `entry_id` of the Config Entry |

### 6.8 Time Handling

All timestamp sensors use `device_class: timestamp` and store values in **UTC**. Home Assistant automatically converts these to the user's local timezone for display.

The integration respects Home Assistant's configured timezone for:
- Midnight/hourly update scheduling
- DST region auto-detection

### 6.9 Repairs Integration

WhenHub registers a repair fix flow via `repairs.py`. HA auto-discovers this file — no explicit registration in `__init__.py` needed.

The fix flow is triggered when the user clicks "Fix" on a WhenHub issue in the HA Repairs panel. Only expiry issues (`translation_key="expired_event"`) are currently implemented.

**Issue lifecycle:**
1. Coordinator update: `_check_expiry_repair(today)` called each cycle
2. If expired + `notify_on_expiry`: `async_create_issue(..., is_fixable=True)`
3. If not expired: `async_delete_issue(...)` — auto-resolves the issue
4. On entry unload: `async_delete_issue` cleanup in `async_unload_entry` for
   `expired_<entry_id>` and `date_order_<entry_id>`
5. On permanent entry removal: `async_remove_entry` deletes all three issue IDs of the
   entry (see "Issue cleanup on unload vs. removal" below)

#### Issue cleanup on unload vs. removal

`async_unload_entry` runs on every reload and on every HA shutdown, so it may only clear
issues that describe the *loaded* state. `entity_deleted_<entry_id>` is deliberately kept
there so the warning survives a restart (#19) — the next `async_setup_entry` re-evaluates
it against the entity registry.

`async_remove_entry(hass, entry)` is the counterpart: Home Assistant calls it only when an
entry is removed for good (deleted in the UI or via `whenhub.delete_event`), after
`async_unload_entry`. It deletes `entity_deleted_<entry_id>`, `expired_<entry_id>` and
`date_order_<entry_id>`. Without it the entity-source warning would outlive the event it
refers to (#28). The other two are included because an entry that never loaded, or that
failed to unload, does not reach the cleanup in `async_unload_entry` at all.

**Important import note:**
- `async_create_issue` / `async_delete_issue` / `IssueSeverity` → `homeassistant.helpers.issue_registry`
- `RepairsFlow` / `ConfirmRepairFlow` → `homeassistant.components.repairs`

### 6.10 Translations

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
- Services (`services.*`: name, description and field texts — validated by hassfest
  against `services.yaml`)
- Service errors (`exceptions.*`: the message of every `ServiceValidationError`)

> **Note:** `format_countdown_text()` outputs German ("5 Tage") regardless of HA language — this is intentional and not covered by the translation system.

### 6.11 manifest.json

| Field | Value | Explanation |
|-------|-------|-------------|
| `domain` | `whenhub` | Unique identifier |
| `config_flow` | `true` | UI configuration |
| `integration_type` | `device` | Creates device entries |
| `iot_class` | `calculated` | Data calculated locally |
| `dependencies` | `["file_upload"]` | Required for image uploads |
| `version` | `x.y.z` | Current version (single source of truth) |

### 6.12 Entity Registry Tracking

WhenHub monitors the HA entity registry for changes to entities configured as date sources. This logic lives in `__init__.py` and is only active for event entries that use at least one entity date source.

#### Two mechanisms run in parallel

**`_check_entity_source_availability(hass, entry)`** — called synchronously in `async_setup_entry` *before* `async_config_entry_first_refresh`. Runs on every setup attempt, including HA restarts and retry cycles.

- If all source entities exist in the registry: deletes any lingering `entity_source_deleted` Repairs issue.
- If any source entity is missing: creates the `entity_source_deleted` Repairs issue and registers a one-shot restore listener (see below).

**`_setup_entity_registry_listener(hass, entry)`** — registered via `hass.bus.async_listen` after a successful setup. Only active while the entry is fully loaded.

| Registry action | `event.data["action"]` | Behaviour |
|---|---|---|
| Entity renamed | `update` (with `changes["entity_id"]`) | Updates the affected config key(s) in `entry.data` with the new entity ID via `async_update_entry` — silent auto-migration, no user interaction needed |
| Entity deleted | `remove` | Creates a `entity_source_deleted` Repairs issue (non-fixable, severity WARNING) |
| Entity created | `create` | Deletes any `entity_source_deleted` issue and triggers an immediate coordinator refresh |

#### Restore listener (retry mode)

During `SETUP_RETRY`, `_setup_entity_registry_listener` is not yet active. To still react when a missing entity comes back, `_check_entity_source_availability` registers a **one-shot restore listener** stored in `hass.data[DOMAIN]["_entity_restore_listeners"][entry_id]`.

On `action="create"` for a known-missing entity, the restore listener:
1. Cancels itself
2. Deletes the Repairs issue
3. Calls `hass.config_entries.async_reload(entry_id)` to trigger a fresh setup immediately

The listener is replaced atomically on each retry (old listener cancelled before registering the new one) and is cleaned up in `async_unload_entry`.

#### Repairs issue details

| Field | Value |
|---|---|
| Issue ID | `entity_deleted_{entry_id}` |
| `is_fixable` | `false` — user must reconfigure via Options Flow |
| Severity | `WARNING` |
| `translation_key` | `entity_source_deleted` |
| Placeholders | `name` (event title), `entity_id` (first missing entity) |

The issue is **not** deleted on entry unload so it persists across HA restarts. On the next `async_setup_entry`, `_check_entity_source_availability` compares the current entity registry state and decides whether to keep or remove the issue. It *is* deleted when the config entry is removed for good — see `async_remove_entry` in 6.9.

### 6.13 Config Entry Updates and Reloads

`async_setup_entry` registers `async_update_listener` via `entry.add_update_listener()`. Home Assistant fires it after every `async_update_entry()` that actually changed something, and it reloads the entry so the coordinator and all platforms pick up the new data.

**Who writes the entry:**

| Writer | Reload |
|---|---|
| Options Flow (`_finalize_options`, `config_flow.py`) | update listener |
| Entity rename auto-migration (`_setup_entity_registry_listener`, 6.12) | update listener |
| `whenhub.update_event` (`services.py`) | its own `async_reload()`, listener suppressed |

**`suppress_update_reload(hass, entry_id)`** is a context manager in `__init__.py` for the third case. It adds the entry ID to a set in `hass.data[DOMAIN]["_suppressed_update_reloads"]`; `async_update_listener` returns without reloading while the ID is in that set, and the `finally` clause always removes it again.

`update_event` needs its own reload because the service must not return before the entities carry the new values. Without the suppression the entry would be reloaded twice per call (#29): Home Assistant starts the listener task eagerly, so the listener's reload begins inside `async_update_entry()`, before the service continues. Because of that eager start the listener always runs while the `with` block is still open — and even without it, it would run at the first suspension point, which is the caller's own `async_reload()` inside the block.

See also the design decision "One reload per update_event" in 5.6.

---

## 7. Resources

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

## 8. Release Process

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

## 9. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-12 | Initial implementation with Trip, Milestone, Anniversary |
| 2.0.0 | 2025-01 | Internationalization (DE/EN), timestamp device_class, relative time display |
| 2.2.1 | 2025-02 | Special Events (holidays, DST), OptionsFlow fixes, removed astronomical events |
| 2.3.0 | 2026-03 | FR08 Calendar entity, FR09 Custom Pattern, FR11 URL/Memo sensors, Bug 003 fixes |
| 3.0.0 | 2026-05 | FR13 Expiry notifications (HA Repairs), Fix #12 image upload validation, Fix #14 entity ID standardization (English type keys, migration v1→v2), #9 Entity date sources (Trip/Milestone/Anniversary), #19 Entity registry tracking (auto-migrate on rename, Repairs on delete) |
| 3.1.0 | 2026-08 | New chapter 5 "Services" with the ADR blocks for name collisions, entity date sources, `SupportsResponse.OPTIONAL` and the import flow (#24); former chapters 5–8 renumbered to 6–9 |
| 3.2.0 | 2026-08 | 6.9 documents `async_remove_entry` and the split between issue cleanup on unload and on removal (#28); corrected the `entity_deleted_{entry_id}` issue ID in 6.12 |
| 3.3.0 | 2026-08 | New section 6.13 on config entry updates and reloads plus the ADR "One reload per update_event" in 5.6 (#29) |
| 3.3.1 | 2026-08 | 3.5 documents the image entity state, `image_last_updated` and `content_type` after the ImageEntity contract fix (#23) |

For detailed release notes with descriptions and issue links, see [`RELEASENOTES.md`](RELEASENOTES.md).

---

*This technical reference serves as the complete specification and documentation of the `whenhub` Home Assistant integration.*
