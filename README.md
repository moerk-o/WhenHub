# WhenHub

[![GitHub Release](https://img.shields.io/github/v/release/moerk-o/WhenHub?style=flat-square)](https://github.com/moerk-o/WhenHub/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1+-41bdf5?style=flat-square&logo=homeassistant)](https://www.home-assistant.io/)

A Home Assistant integration for tracking various events and important dates. WhenHub provides countdown sensors, status information, and visual representations for your events.

## Overview

**The origin story:** The kids kept asking "How much longer until vacation?" or "How many days until my birthday?". I thought, there's got to be something I can do with Home Assistant! Now WhenHub displays an image of the event on the tablet with a big number showing the remaining days and the duration as text below.

### Event Types

**Trip** - Multi-day events like vacations or visiting grandma
**Milestone** - One-time important dates like school events or 'when is the new pet coming'
**Anniversary** - Yearly recurring events like birthdays or holidays
**Special Event** - Predefined holidays like Christmas, Easter, DST changes — and your own **Custom Patterns**
**WhenHub Calendar** - Not an event type per se, but a companion feature: aggregates your WhenHub events into Home Assistant's built-in calendar view

Events are set up in the user interface. For automations and scripts, three
[services](#services) create, change and remove events.

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Search for "WhenHub"
3. Click **Download**
4. Restart Home Assistant
5. Go to **Settings** → **Devices & Services** → **Add Integration**
6. Search for "WhenHub" and follow the configuration wizard

### Manual Installation

1. Download the latest version from the [Releases page](https://github.com/moerk-o/WhenHub/releases)
2. Extract the files to the `custom_components/whenhub` directory of your Home Assistant installation
3. Restart Home Assistant
4. Go to **Settings** → **Devices & Services** → **Add Integration**
5. Search for "WhenHub" and follow the configuration wizard

## Trip Events

Trip events have a **start date** and **end date** and provide comprehensive tracking functions for multi-day events.

### Configuration

When setting up a Trip event, you configure:

- **Start Date**: When the trip begins (Format: YYYY-MM-DD) — or use a date/timestamp entity as source
- **End Date**: When the trip ends (Format: YYYY-MM-DD) — or use a date/timestamp entity as source
- **Image** *(optional)*: Upload a file or enter a path — [see Image Management](#image-management). Default: blue airplane icon.
- **URL** *(optional)*: A link to a booking page, website or any related URL.
- **Memo** *(optional)*: Free-text notes — supports Markdown.
- **Notify when expired** *(optional)*: Create a notification in [HA Repairs](#expiry-notifications) when the trip's end date has passed. Default: off.

> **Entity as date source:** Enable the toggle next to a date field to pick a HA entity (`device_class: date` or `timestamp`) instead of a fixed date. The coordinator reads the entity's state on every update. When an entity source is active, the **Event Date** sensor shows a different icon to indicate the dynamic source.

### Available Entities

#### Sensors
- **Event Date** - Start date of the trip (ISO 8601 timestamp, displays as relative time) — different icon when any date comes from an entity
  - **Attributes**:
    - `event_name` - Name of the event
    - `event_type` - Type of event (trip)
    - `end_date` - End date (ISO format)
    - `trip_duration_days` - Total trip duration in days
    - `breakdown_years` - Years component of countdown until start
    - `breakdown_months` - Months component of countdown until start
    - `breakdown_weeks` - Weeks component of countdown until start
    - `breakdown_days` - Days component of countdown until start
    - `start_date_source_entity` *(only when start date comes from entity)* - Entity ID of the start date source
    - `end_date_source_entity` *(only when end date comes from entity)* - Entity ID of the end date source
- **Days Until Start** -  Days until trip begins (can become negative if date has passed)
- **Days Until End** - Days until trip ends (can become negative if date has passed)
- **Trip Left Days** - Remaining days during the trip
- **Trip Left Percent** - Remaining trip percentage (100% before start, decreases during trip, 0% after end)
- **URL** *(optional)* — Created only when a URL is configured
- **Memo** *(optional)* — Created only when a memo is configured

#### Binary Sensors
- **Trip Starts Today** - `true` when the trip starts today
- **Trip Active Today** - `true` when the trip is active today
- **Trip Ends Today** - `true` when the trip ends today

#### Image
- **Event Image** — [→ Image Management](#image-management)

## Milestone Events

Milestone events have a single **target date** and focus on the countdown to this important date.

### Configuration

When setting up a Milestone event, you configure:

- **Target Date**: The important date (Format: YYYY-MM-DD) — or use a date/timestamp entity as source
- **Image** *(optional)*: Upload a file or enter a path — [see Image Management](#image-management). Default: red flag icon.
- **URL** *(optional)*: A link to a website or any related URL.
- **Memo** *(optional)*: Free-text notes — supports Markdown.
- **Notify when expired** *(optional)*: Create a notification in [HA Repairs](#expiry-notifications) when the target date has passed. Default: off.

> **Entity as date source:** Enable the toggle next to the date field to pick a HA entity (`device_class: date` or `timestamp`) instead of a fixed date. When active, the **Event Date** sensor shows a different icon to indicate the dynamic source.

### Available Entities

#### Sensors
- **Event Date** - Target date of the milestone (ISO 8601 timestamp, displays as relative time) — different icon when date comes from an entity
  - **Attributes**:
    - `event_name` - Name of the event
    - `event_type` - Type of event (milestone)
    - `breakdown_years` - Years component of countdown until target
    - `breakdown_months` - Months component of countdown until target
    - `breakdown_weeks` - Weeks component of countdown until target
    - `breakdown_days` - Days component of countdown until target
    - `date_source_entity` *(only when date comes from entity)* - Entity ID of the date source
- **Days Until** - Days until milestone (can become negative if date has passed)
- **URL** *(optional)* — Created only when a URL is configured
- **Memo** *(optional)* — Created only when a memo is configured

#### Binary Sensors
- **Is Today** - `true` when today is the milestone day

#### Image
- **Event Image** — [→ Image Management](#image-management)

## Anniversary Events

Anniversary events repeat annually based on an **original date** and provide both retrospective and prospective functions.

### Configuration

When setting up an Anniversary event, you configure:

- **Original Date**: The date of the first event (Format: YYYY-MM-DD) — or use a date/timestamp entity as source
- **Image** *(optional)*: Upload a file or enter a path — [see Image Management](#image-management). Default: pink heart icon.
- **URL** *(optional)*: A link to a website or any related URL.
- **Memo** *(optional)*: Free-text notes — supports Markdown.

> **Entity as date source:** Enable the toggle next to the date field to pick a HA entity (`device_class: date` or `timestamp`) instead of a fixed date. When active, the **Event Date** sensor shows a different icon to indicate the dynamic source.

### Available Entities

#### Sensors
- **Event Date** - Date of the next anniversary (ISO 8601 timestamp, displays as relative time) — different icon when date comes from an entity
  - **Attributes**:
    - `event_name` - Name of the event
    - `event_type` - Type of event (anniversary)
    - `initial_date` - Original date (ISO format)
    - `years_on_next` - Number of years at next anniversary
    - `breakdown_years` - Years component of countdown until next anniversary
    - `breakdown_months` - Months component of countdown until next anniversary
    - `breakdown_weeks` - Weeks component of countdown until next anniversary
    - `breakdown_days` - Days component of countdown until next anniversary
    - `date_source_entity` *(only when date comes from entity)* - Entity ID of the date source
- **Days Until Next** - Days until next anniversary
- **Days Since Last** - Days since last anniversary
- **Occurrences Count** - Number of past occurrences
- **Next Date** - Date of next anniversary (ISO 8601 timestamp)
- **Last Date** - Date of last anniversary (ISO 8601 timestamp)
- **URL** *(optional)* — Created only when a URL is configured
- **Memo** *(optional)* — Created only when a memo is configured

#### Binary Sensors
- **Is Today** - `true` when today is an anniversary day

#### Image
- **Event Image** — [→ Image Management](#image-management)

### Leap Year Handling
Anniversary events handle leap years intelligently: When the original date is February 29th, non-leap years automatically use February 28th.

## Special Events

Special events track holidays that repeat annually. These include both fixed-date holidays and calculated events with complex date algorithms.

### Configuration

When setting up a Special Event, you configure:

- **Event Category**: Choose from 4 categories (Traditional Holidays, Calendar Holidays, Daylight Saving Time, Custom Pattern)
- **Special Event Type**: Choose from 13 predefined holidays — or define your own Custom Pattern
- **Image** *(optional)*: Upload a file or enter a path — [see Image Management](#image-management). Default: purple star icon.
- **URL** *(optional)*: A link to a website or any related URL.
- **Memo** *(optional)*: Free-text notes — supports Markdown.

### Available Entities

#### Sensors
- **Days Until** - Days until next occurrence
- **Days Since Last** - Days since last occurrence
- **Event Date** - Date of the next occurrence (ISO 8601 timestamp, displays as relative time)
  - **Attributes**:
    - `event_name` - Name of the event
    - `event_type` - Type of event (special)
    - `special_type` - Specific holiday type (e.g., "christmas", "easter")
    - `special_name` - Display name of the holiday
    - `breakdown_years` - Years component of countdown until next
    - `breakdown_months` - Months component of countdown until next
    - `breakdown_weeks` - Weeks component of countdown until next
    - `breakdown_days` - Days component of countdown until next
- **Next Date** - Date of next occurrence (ISO 8601 timestamp)
- **Last Date** - Date of last occurrence (ISO 8601 timestamp)
- **URL** *(optional)* — Created only when a URL is configured
- **Memo** *(optional)* — Created only when a memo is configured

#### Binary Sensors
- **Is Today** - `true` when today is the special event day
- **DST Active** - `true` when summer time (DST) is currently active (only for DST events)

#### Image
- **Event Image** — [→ Image Management](#image-management)

### Available Special Events

Special Events are organized into 4 categories:

#### Traditional Holidays (11 Events)
Fixed and calculated events celebrating traditional holidays:

**Fixed Date Events:**
- **Christmas Eve** - December 24th
- **Christmas Day** - December 25th
- **Boxing Day** - December 26th
- **Halloween** - October 31st
- **St. Nicholas Day** - December 6th

**Calculated Events using the Gauss Easter Algorithm:**
- **Easter Sunday** - Base calculation for moveable feasts
- **Pentecost Sunday** - 49 days after Easter

**Advent Sundays (calculated from Christmas Eve):**
- **1st Advent** - 4th Sunday before Christmas Eve
- **2nd Advent** - 3rd Sunday before Christmas Eve
- **3rd Advent** - 2nd Sunday before Christmas Eve
- **4th Advent** - Sunday before Christmas Eve

#### Calendar Holidays (2 Events)
Fixed calendar events marking year transitions:
- **New Year's Day** - January 1st
- **New Year's Eve** - December 31st

#### Daylight Saving Time (DST)
Track when clocks change for summer and winter time. Supports multiple regions with their specific DST rules.

**Supported Regions** (auto-detected from your timezone, but can be changed):
- **EU** - Last Sunday of March (summer) / Last Sunday of October (winter)
- **USA** - 2nd Sunday of March / 1st Sunday of November
- **Australia** - 1st Sunday of October / 1st Sunday of April
- **New Zealand** - Last Sunday of September / 1st Sunday of April

**Event Types:**
- **Next Change** - Countdown to the next DST transition (summer or winter)
- **Summer Time** - Countdown to the next start of summer time
- **Winter Time** - Countdown to the next start of winter time

**Additional Sensors for DST:**
- **DST Active** - Binary sensor showing if summer time is currently active (dynamic icon changes with state)

#### Custom Pattern

Custom Pattern lets you define your own repeating rule — from simple "every Monday" to complex "4th Thursday of November every year". The pattern is based on the [RFC 5545 iCalendar RRULE standard](https://www.rfc-editor.org/rfc/rfc5545), the same standard used by Google Calendar, Outlook, and Apple Calendar.

##### Why Custom Pattern?

The predefined holidays cover common events, but many recurring dates follow weekday-based rules that shift every year. Without Custom Pattern you would have to update those dates manually each year. Examples (sorted by calendar date):

| # | Event | Rule |
|---|-------|------|
| 1 | **Early May Bank Holiday** (UK) | 1st Monday in May |
| 2 | **Mother's Day** (DE/AT/CH/UK/...) | 2nd Sunday in May |
| 3 | **Memorial Day** (US) | Last Monday in May |
| 4 | **Tag der Deutschen Einheit** (DE) | 3rd October (fixed) |
| 5 | **Väterdag** (Sweden) | 2nd Sunday in November |
| 6 | **Thanksgiving** (US) | 4th Thursday in November |
| 7 | **Your team meeting** | Every Monday |
| 8 | **Medication reminder** | Every 3 days |
| 9 | **Quarterly review** | First Monday of every 3rd month |

→ [See example configurations below](#example-configurations)

##### Configuration Flow

Custom Pattern uses a guided multi-step setup. The steps you see depend on the frequency you choose:

**Step 1 — Frequency, Anchor Date, Interval**

| Field | Description |
|-------|-------------|
| Frequency | Yearly / Monthly / Weekly / Daily |
| Anchor Date | The starting point for the pattern (e.g. `2020-01-01`). The first occurrence is calculated from here — past dates are fine. |
| Interval | Repeat every N periods. `1` = every year/month/week/day. `2` = every other. |

**Step 2 — Period-specific rules**

Depending on the frequency, you then define how the day within the period is selected:

*Yearly:* Choose the **month** and then the day rule.
*Monthly:* Choose the day rule directly.
*Weekly:* Choose one or more **weekdays** (multi-select, e.g. Mon + Wed + Fri).
*Daily:* No extra step — goes directly to the end condition.

**Day rules (Yearly and Monthly):**

| Rule | Meaning | Example |
|------|---------|---------|
| Nth weekday | Nth occurrence of a specific weekday | 2nd Sunday in May → Mother's Day |
| Last weekday | Last occurrence of a specific weekday in the period | Last Monday in May → Memorial Day |
| Fixed day | A fixed calendar day of the month | 15th of each month |

**Step 3 — End Condition**

| Option | Meaning |
|--------|---------|
| No end | Repeats forever |
| Until a date | Repeats until a specific date (inclusive) |
| After N occurrences | Stops after exactly N occurrences |

**Step 4 — Image, URL, Memo and Notifications**

- **Image** *(optional)*: Upload or enter path — [see Image Management](#image-management).
- **URL** *(optional)*: A link to a website or any related URL.
- **Memo** *(optional)*: Free-text notes — supports Markdown.
- **Notify when expired** *(optional)*: Only shown when an end condition is set. Create a notification in [HA Repairs](#expiry-notifications) when the pattern has no more future occurrences. Default: off.

##### Example Configurations

**1 — Early May Bank Holiday** (1st Monday in May, UK):
- Frequency: Yearly, Interval: 1, Anchor: 2020-01-01
- Month: May
- Day rule: Nth weekday → 1st → Monday
- End: No end
- 2026: **May 4**

**2 — Mother's Day** (2nd Sunday in May, DE/AT/CH/UK and many others):
- Frequency: Yearly, Interval: 1, Anchor: 2020-01-01
- Month: May
- Day rule: Nth weekday → 2nd → Sunday
- End: No end
- 2026: **May 10**

**3 — Memorial Day** (Last Monday in May, US):
- Frequency: Yearly, Interval: 1, Anchor: 2020-01-01
- Month: May
- Day rule: Last weekday → Monday
- End: No end
- 2026: **May 25**

**4 — Tag der Deutschen Einheit** (3rd October, fixed date):
- Frequency: Yearly, Interval: 1, Anchor: 2020-01-01
- Month: October
- Day rule: Fixed day → 3
- End: No end
- 2026: **October 3**

**5 — Väterdag** (2nd Sunday in November, Sweden):
- Frequency: Yearly, Interval: 1, Anchor: 2020-01-01
- Month: November
- Day rule: Nth weekday → 2nd → Sunday
- End: No end
- 2026: **November 8**

**6 — Thanksgiving** (4th Thursday in November, US):
- Frequency: Yearly, Interval: 1, Anchor: 2020-01-01
- Month: November
- Day rule: Nth weekday → 4th → Thursday
- End: No end
- 2026: **November 26**

**7 — Your team meeting** (every Monday):
- Frequency: Weekly, Interval: 1, Anchor: any Monday
- Weekdays: Monday
- End: No end

**8 — Medication reminder** (every 3 days):
- Frequency: Daily, Interval: 3, Anchor: first intake date
- End: No end (or after N occurrences if the course is finite)

**9 — Quarterly review** (first Monday of every 3rd month):
- Frequency: Monthly, Interval: 3, Anchor: 2026-01-01
- Day rule: Nth weekday → 1st → Monday
- End: No end
- Next after 2026-04-06: **July 6, 2026**

##### Available Entities

###### Sensors
- **Days Until Start** — Days until the next occurrence (0 on occurrence day, 1 = tomorrow, etc.)
- **Days Since Last** — Days since the most recent past occurrence
- **Event Date** — Timestamp of the next occurrence (ISO 8601)
  - **Attributes**: `cp_freq`, `occurrence_count`
- **Next Date** — Timestamp of the next *future* occurrence (never today, even when today is an occurrence)
- **Last Date** — Timestamp of the most recent occurrence (including today)
- **Occurrence Count** — How many times the pattern has fired since the anchor date (counting today)
- **URL** *(optional)* — Created only when a URL is configured
- **Memo** *(optional)* — Created only when a memo is configured

###### Binary Sensors
- **Is Today** — `true` when today is an occurrence day

##### The Anchor Date

The anchor date is important: it defines where counting starts. For Yearly and Monthly patterns it influences which day is selected; for Weekly it determines the phase (i.e. which weeks are "on" when using an interval > 1); for Daily it sets the starting point of the interval.

**Tip:** For patterns like "every other Monday", set the anchor date to a Monday you want to be an occurrence — the pattern then fires on every second Monday counting from there.

##### Occurrence Count vs. Days Until

On an occurrence day:
- `is_today` = `on`
- `last_date` = today
- `next_date` = tomorrow (or the next future occurrence)
- `days_until` = days to the next *future* occurrence (not 0)
- `occurrence_count` = total occurrences so far including today

### Date Calculation Details

#### Easter Algorithm
Special Events uses the **Gauss Easter Algorithm** to calculate Easter dates without requiring lunar data or external dependencies. This algorithm:
- Works for any year in the Gregorian calendar
- Calculates Western (Catholic/Protestant) Easter
- Handles leap years and calendar irregularities automatically
- Provides the foundation for all Easter-dependent holidays

#### Advent Calculation
Advent Sundays are calculated by:
1. Finding Christmas Eve (December 24th)
2. Determining the day of the week
3. Calculating backwards to find the 4th, 3rd, 2nd, and 1st Sundays before
4. Special handling when Christmas Eve itself falls on a Sunday

## WhenHub Calendar

The WhenHub Calendar integrates your WhenHub events into Home Assistant's built-in calendar view. Instead of creating sensors and binary sensors, it creates a **calendar entity** that makes your events visible in HA's calendar dashboard — just like any other calendar integration (Google Calendar, iCloud, etc.).

### Configuration

When setting up a WhenHub Calendar, you configure:

1. **Scope** — Which events should appear in this calendar:
   - **All Events** — Every configured WhenHub event (Trips, Milestones, Anniversaries, Special Events)
   - **Filter by Type** — Only show selected event types (e.g. Trips and Anniversaries only)
   - **Select Specific Events** — Cherry-pick individual events by name

The calendar name is suggested automatically based on your HA language setting ("WhenHub Calendar" / "WhenHub Kalender") and auto-incremented if a name is already taken. You can change the name in HA's built-in "Device created" dialog.

### Multiple Calendars

For most users, **a single WhenHub Calendar showing all events is all you need** — just set the scope to "All Events" and you're done.

If you want more control, you can create additional WhenHub Calendars with different scopes. For example:
- One calendar showing all events
- One calendar showing only trips
- One calendar showing only anniversaries

Each calendar appears as a separate entry in the Home Assistant calendar view and the integrations UI. Multiple calendars are an optional advanced feature — there's no requirement to create more than one.

### Available Entities

#### Calendar
- **Calendar entity** — The calendar itself. Appears in HA's calendar dashboard and shows all scoped events.
  - **State `on`**: An event is currently active today (trip is running, milestone/anniversary/special is today)
  - **State `off`**: No active event today

### How Events Appear in the Calendar

| WhenHub Type | In HA Calendar |
|---|---|
| Trip | Shown as a multi-day event spanning the full trip duration |
| Milestone | Shown as a one-day event on the target date |
| Anniversary | Shown annually — e.g., "Birthday Jon (16.)" for the 16th occurrence |
| Special Event | Shown annually on the calculated holiday date |
| Custom Pattern | All occurrences within the calendar's view range are shown as one-day events |

### Options Flow

The calendar configuration can be changed at any time:

1. Go to **Settings** → **Devices & Services** → **WhenHub**
2. Click **Configure** on the desired calendar entry
3. Adjust the scope, type filter, or event selection

After saving, the calendar reloads automatically and the description in the integrations UI updates to reflect the new configuration.

## Advanced Features

### Image Management

Every WhenHub event has an **Event Image** entity. When no image is configured, a default SVG icon is generated automatically.

#### Adding an Image

In the configuration form, two options are available — use one or both:

1. **Upload** — Drag & drop or click to select a file directly in the HA config flow. The image is stored inside the config entry — no files to manage on the server. Supported formats: JPEG, PNG, WebP, GIF. Maximum file size: 5 MB.
2. **Path** — Enter a path to an image already on your HA server, e.g. `/local/images/trip.jpg` (files placed in the `www/` directory of your HA config).

**Priority:** If both are provided, the upload takes precedence over the path.

#### Changing or Removing an Image

Go to **Settings → Devices & Services → WhenHub**, click **Configure** on the event, and:

- Upload a new file to replace the current image
- Enable **Remove current image** and save — the image will be removed and replaced by the default icon
- Leave both fields empty to keep the current image unchanged

#### Image Entity

The `Event Image` entity appears in every event's device and can be used in dashboards, picture-entity cards, or automations.

**Attributes:**

| Attribute | Description |
|---|---|
| `image_type` | `"user_defined"` (custom) or `"system_defined"` (default icon) |
| `image_path` | File path for path-based images, `"base64_data"` for uploads, or `"default_svg"` |

### Countdown Breakdown Attributes

The `event_date` sensor provides breakdown attributes for building localized countdown text:
- `breakdown_years` - Years component (integer)
- `breakdown_months` - Months component (integer)
- `breakdown_weeks` - Weeks component (integer)
- `breakdown_days` - Days component (integer)

These values are calculated using approximations (365 days/year, 30 days/month) for consistent results. Use these attributes in Lovelace cards or templates to create formatted countdown text in your preferred language.

### Expiry Notifications

WhenHub can notify you when an event's date has passed and the event is no longer relevant. This feature uses Home Assistant's built-in **Repairs** panel.

**Supported event types:**
- **Trip** — notifies when the end date has passed
- **Milestone** — notifies when the target date has passed
- **Custom Pattern** — notifies when the pattern has no more future occurrences (only available when an end condition is configured)

**How to enable:**
Enable **Notify when expired** in the event's configuration (or Options Flow). The toggle is off by default.

**How it works:**
1. WhenHub detects on every update cycle that the event has expired
2. A fixable issue appears in **Settings → System → Repairs**
3. Click **Fix** to open a confirmation dialog
4. Confirm to permanently remove the event and all its entities

> **Before confirming:** Check if any dashboards, automations, or scripts reference this event's entities — they will stop working after removal. You can also dismiss the notification to keep the event unchanged.

**Auto-resolve:** If you update the event's dates (via Options Flow) so that it is no longer expired, the Repairs notification disappears automatically on the next update cycle.

### Options Flow

All event configurations can be edited after initial setup via the **Options Flow**:

1. Go to **Settings** → **Devices & Services** → **WhenHub**
2. Click **Configure** on the desired event
3. Modify the settings for the respective event (Trip, Milestone, or Anniversary) and save

**Note:** Converting between event types (e.g., Trip to Anniversary) is not possible.

All sensors are automatically updated with the new data.

## Services

WhenHub events can be created, changed and removed from automations and scripts. Three
services cover what the configuration UI does:

| Service | Purpose |
|---|---|
| `whenhub.create_event` | Create a Trip, Milestone, Anniversary, Special Event or DST event |
| `whenhub.update_event` | Change fields of an existing event |
| `whenhub.delete_event` | Remove an event including its device and entities |

The services are registered when the integration loads, so at least one WhenHub event or
calendar has to exist before they show up in **Developer Tools → Actions**.

**Custom Pattern events can only be created in the user interface.** Their twelve
interdependent pattern fields need the guided configuration flow. `update_event` can
still change the generic fields (name, image, URL, memo, expiry notification) of a Custom
Pattern event, and `delete_event` works on it like on any other event.

### `whenhub.create_event`

```yaml
action: whenhub.create_event
data:
  event_type: trip
  name: Denmark 2026
  start_date: "2026-07-12"
  end_date: "2026-07-26"
  image_path: /local/whenhub/denmark.jpg
  memo: Ferry at 9 am
  notify_on_expiry: true
response_variable: created
```

| Parameter | Required | Description |
|---|---|---|
| `event_type` | yes | `trip`, `milestone`, `anniversary`, `special` or `dst` |
| `name` | yes | Becomes the entry title and the device name |
| `auto_rename` | no (`false`) | Append a number instead of failing when the name is taken |
| `start_date`, `end_date` | Trip | ISO dates, `YYYY-MM-DD`. The end date must be after the start date |
| `target_date` | Milestone, Anniversary | ISO date. For an anniversary this is the original date, e.g. the year of birth |
| `start_date_entity`, `end_date_entity`, `target_date_entity` | no | Take the date from an entity instead. Needs device class `date` or `timestamp`; replaces the fixed date of the same field |
| `special_type` | Special | Holiday key, e.g. `easter`, `christmas_eve`, `new_year`. The category is derived from it |
| `dst_region` | DST | `eu`, `usa`, `australia` or `new_zealand` |
| `dst_type` | no (`next_change`) | `next_change`, `next_summer` or `next_winter` |
| `image_path` | no | Path or URL of an image. Uploading a file is only possible in the UI |
| `url` | no | Creates the URL sensor |
| `memo` | no | Markdown text, creates the memo sensor |
| `notify_on_expiry` | no (`false`) | Only for `trip` and `milestone` — other types cannot expire |

A name that already exists is rejected. This protects against a faulty automation that
fires every night and would otherwise pile up "Denmark 2026 2", "Denmark 2026 3" and so
on. Pass `auto_rename: true` when you do want the numbering, for example when creating a
list of events in a loop.

Response:

```yaml
device_id: 1a2b3c4d5e6f7890abcdef1234567890
entry_id: 01M177T7QDGBASRJX2GNYZGJP4
name: Denmark 2026
event_type: trip
```

`name` is the name that was actually used, which differs from the one you passed when
`auto_rename` stepped in. Keep the `device_id` if the automation wants to change or
remove the event later.

### `whenhub.update_event`

```yaml
action: whenhub.update_event
data:
  device_id: 1a2b3c4d5e6f7890abcdef1234567890
  end_date: "2026-08-02"
  memo: Ferry moved to 11 am
response_variable: result
```

| Parameter | Required | Description |
|---|---|---|
| `device_id` | yes | The event to change. Every WhenHub event is a device |
| `name` | no | Rename the event. Entity IDs stay as they are — that is Home Assistant behaviour |
| `start_date`, `end_date`, `target_date` | no | Set a fixed date |
| `start_date_entity`, `end_date_entity`, `target_date_entity` | no | Switch the field to an entity source |
| `replace_date_source` | no (`false`) | Allow a fixed date to overwrite an active entity source |
| `special_type`, `dst_region`, `dst_type` | no | Only on the matching event type |
| `image_path`, `url`, `memo` | no | An empty string clears the field and removes the URL or memo sensor |
| `notify_on_expiry` | no | Only for trips, milestones, and Custom Patterns that have an end condition |

Only the fields you pass are changed; everything else stays untouched. The event type
itself cannot be changed, and neither can a field that does not belong to the event type
— `target_date` on a trip is an error, not a silent no-op. After a successful change the
event is reloaded, so its sensors already show the new values when the call returns.

Setting a fixed date on a field that currently reads from an entity is refused, because
silently dropping the entity source would be a surprise. Add `replace_date_source: true`
when that is what you mean:

```yaml
action: whenhub.update_event
data:
  device_id: 1a2b3c4d5e6f7890abcdef1234567890
  target_date: "2026-09-01"
  replace_date_source: true
```

The other direction — pointing a field that holds a fixed date at an entity — needs no
extra parameter, as nothing is lost.

Response:

```yaml
device_id: 1a2b3c4d5e6f7890abcdef1234567890
name: Denmark 2026
changed:
  end_date:
    old: "2026-07-26"
    new: "2026-08-02"
  memo:
    old: Ferry at 9 am
    new: Ferry moved to 11 am
```

`changed` lists only the fields whose value actually differs. A call that sets everything
to the value it already has returns `changed: {}` and does not reload the event. When a
field switches between a fixed date and an entity, both keys appear:

```yaml
changed:
  target_date:
    old: "2026-07-01"
    new: null
  target_date_entity:
    old: null
    new: sensor.next_appointment
```

### `whenhub.delete_event`

> **Warning:** `delete_event` removes the event immediately. There is no confirmation
> dialog and no undo. The config entry, the device, and every sensor, binary sensor and
> image entity of that event are gone, and any dashboard card, automation or script that
> references those entities stops working. Check what depends on the event before you
> call this from an automation.

```yaml
action: whenhub.delete_event
data:
  device_id: 1a2b3c4d5e6f7890abcdef1234567890
response_variable: removed
```

| Parameter | Required | Description |
|---|---|---|
| `device_id` | yes | The event to remove |

An open expiry notification in **Settings → System → Repairs** for that event is removed
with it.

Response:

```yaml
device_id: 1a2b3c4d5e6f7890abcdef1234567890
entry_id: 01M177T7QDGBASRJX2GNYZGJP4
name: Denmark 2026
event_type: trip
removed_entities:
  - binary_sensor.denmark_2026_trip_active_today
  - binary_sensor.denmark_2026_trip_ends_today
  - binary_sensor.denmark_2026_trip_starts_today
  - image.denmark_2026_event_image
  - sensor.denmark_2026_days_until
  - sensor.denmark_2026_days_until_end
  - sensor.denmark_2026_event_date
  - sensor.denmark_2026_trip_left_days
  - sensor.denmark_2026_trip_left_percent
```

`removed_entities` is read before the event is removed, so the list is complete — useful
for reporting back what disappeared.

### Responses

All three services use `SupportsResponse.OPTIONAL`. Add `response_variable` to work with
the result; leave it out and the service simply runs, which is what you want behind a
dashboard button or in a script that does not care about the details.

### Example: notification with a delete button

Two automations. The first notices that a trip is over and sends a push notification with
two buttons, the second acts on the answer and reports what was removed.

```yaml
automation:
  - alias: "WhenHub: offer to remove the finished trip"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.denmark_2026_days_until_end
        below: 0
    actions:
      - action: notify.mobile_app_pixel
        data:
          title: Denmark 2026 is over
          message: Remove the event and all its entities?
          data:
            actions:
              - action: WHENHUB_DELETE_DENMARK
                title: Delete
              - action: WHENHUB_KEEP
                title: Keep

  - alias: "WhenHub: remove the trip when confirmed"
    triggers:
      - trigger: event
        event_type: mobile_app_notification_action
        event_data:
          action: WHENHUB_DELETE_DENMARK
    actions:
      - action: whenhub.delete_event
        data:
          device_id: 1a2b3c4d5e6f7890abcdef1234567890
        response_variable: removed
      - action: notify.mobile_app_pixel
        data:
          title: WhenHub event removed
          message: >-
            {{ removed.name }} is gone, including
            {{ removed.removed_entities | count }} entities.
```

Find the `device_id` under **Settings → Devices & Services → WhenHub → <event>**; it is
the last part of the device page URL. In the visual automation editor the `device_id`
field shows a device picker instead.

If you would rather let WhenHub ask on its own, enable `notify_on_expiry` on the event:
Home Assistant then shows a repair notification with a **Fix** button that removes the
event after a confirmation. See [Expiry Notifications](#expiry-notifications).

## Technical Details

| Property | Value |
|----------|-------|
| Update Interval | Once per hour |
| IoT Class | `calculated` |
| Platforms | Sensor, Binary Sensor, Image, Calendar |
| Config Flow | Full UI configuration |
| Services | `create_event`, `update_event`, `delete_event` |

## Localization

The integration supports multiple languages through Home Assistant's translation system. All sensor names, configuration labels, and event names are translated.

**Currently supported languages:**

- English (fallback)
- German (Deutsch)

## Contributing

This project is open source and contributions are warmly welcomed! Issues for bugs or feature requests are just as appreciated as pull requests for code improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Development assisted by [Claude](https://claude.ai/) (Anthropic)

---

⭐ **Like WhenHub?** Instead of buying me a coffee, give the project a star on GitHub!
