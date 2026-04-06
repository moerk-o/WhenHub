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

- **Start Date**: When the trip begins (Format: YYYY-MM-DD)
- **End Date**: When the trip ends (Format: YYYY-MM-DD)
- **Image Path** *(optional)*:
  - Leave empty = Automatically generated default image (blue airplane icon)
  - File path = e.g., `/local/images/denmark.jpg` for custom images
  - Base64 string = Directly embedded encoded image

### Available Entities

#### Sensors
- **Event Date** - Start date of the trip (ISO 8601 timestamp, displays as relative time)
  - **Attributes**:
    - `event_name` - Name of the event
    - `event_type` - Type of event (trip)
    - `end_date` - End date (ISO format)
    - `trip_duration_days` - Total trip duration in days
    - `breakdown_years` - Years component of countdown until start
    - `breakdown_months` - Months component of countdown until start
    - `breakdown_weeks` - Weeks component of countdown until start
    - `breakdown_days` - Days component of countdown until start
- **Days Until Start** -  Days until trip begins (can become negative if date has passed)
- **Days Until End** - Days until trip ends (can become negative if date has passed)
- **Trip Left Days** - Remaining days during the trip
- **Trip Left Percent** - Remaining trip percentage (100% before start, decreases during trip, 0% after end)

#### Binary Sensors
- **Trip Starts Today** - `true` when the trip starts today
- **Trip Active Today** - `true` when the trip is active today
- **Trip Ends Today** - `true` when the trip ends today

#### Image
- **Event Image** - Shows the configured image or default image
  - **Attributes**: 
    - `image_type` - "user_defined" (custom image) or "system_defined" (default icon)
    - `image_path` - Path to image, "base64_data" or "default_svg"

## Milestone Events

Milestone events have a single **target date** and focus on the countdown to this important date.

### Configuration

When setting up a Milestone event, you configure:

- **Target Date**: The important date (Format: YYYY-MM-DD)
- **Image Path** *(optional)*:
  - Leave empty = Automatically generated default image (red flag icon)
  - File path = e.g., `/local/images/birthday.jpg` for custom images
  - Base64 string = Directly embedded encoded image

### Available Entities

#### Sensors
- **Event Date** - Target date of the milestone (ISO 8601 timestamp, displays as relative time)
  - **Attributes**:
    - `event_name` - Name of the event
    - `event_type` - Type of event (milestone)
    - `breakdown_years` - Years component of countdown until target
    - `breakdown_months` - Months component of countdown until target
    - `breakdown_weeks` - Weeks component of countdown until target
    - `breakdown_days` - Days component of countdown until target
- **Days Until** - Days until milestone (can become negative if date has passed)

#### Binary Sensors
- **Is Today** - `true` when today is the milestone day

#### Image
- **Event Image** - Shows the configured image or default image
  - **Attributes**: 
    - `image_type` - "user_defined" (custom image) or "system_defined" (default icon)
    - `image_path` - Path to image, "base64_data" or "default_svg"

## Anniversary Events

Anniversary events repeat annually based on an **original date** and provide both retrospective and prospective functions.

### Configuration

When setting up an Anniversary event, you configure:

- **Original Date**: The date of the first event (Format: YYYY-MM-DD)
- **Image Path** *(optional)*:
  - Leave empty = Automatically generated default image (pink heart icon)
  - File path = e.g., `/local/images/wedding.jpg` for custom images
  - Base64 string = Directly embedded encoded image

### Available Entities

#### Sensors
- **Event Date** - Date of the next anniversary (ISO 8601 timestamp, displays as relative time)
  - **Attributes**:
    - `event_name` - Name of the event
    - `event_type` - Type of event (anniversary)
    - `initial_date` - Original date (ISO format)
    - `years_on_next` - Number of years at next anniversary
    - `breakdown_years` - Years component of countdown until next anniversary
    - `breakdown_months` - Months component of countdown until next anniversary
    - `breakdown_weeks` - Weeks component of countdown until next anniversary
    - `breakdown_days` - Days component of countdown until next anniversary
- **Days Until Next** - Days until next anniversary
- **Days Since Last** - Days since last anniversary
- **Occurrences Count** - Number of past occurrences
- **Next Date** - Date of next anniversary (ISO 8601 timestamp)
- **Last Date** - Date of last anniversary (ISO 8601 timestamp)

#### Binary Sensors
- **Is Today** - `true` when today is an anniversary day

#### Image
- **Event Image** - Shows the configured image or default image
  - **Attributes**: 
    - `image_type` - "user_defined" (custom image) or "system_defined" (default icon)
    - `image_path` - Path to image, "base64_data" or "default_svg"

### Leap Year Handling
Anniversary events handle leap years intelligently: When the original date is February 29th, non-leap years automatically use February 28th.

## Special Events

Special events track holidays that repeat annually. These include both fixed-date holidays and calculated events with complex date algorithms.

### Configuration

When setting up a Special Event, you configure:

- **Event Category**: Choose from 4 categories (Traditional Holidays, Calendar Holidays, Daylight Saving Time, Custom Pattern)
- **Special Event Type**: Choose from 13 predefined holidays — or define your own Custom Pattern
- **Image Path** *(optional)*:
  - Leave empty = Automatically generated default image (purple star icon)
  - File path = e.g., `/local/images/christmas.jpg` for custom images
  - Base64 string = Directly embedded encoded image

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

#### Binary Sensors
- **Is Today** - `true` when today is the special event day
- **DST Active** - `true` when summer time (DST) is currently active (only for DST events)

#### Image
- **Event Image** - Shows the configured image or default purple star icon
  - **Attributes**: 
    - `image_type` - "user_defined" (custom image) or "system_defined" (default icon)
    - `image_path` - Path to image, "base64_data" or "default_svg"

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

WhenHub supports various types of images for your events:

1. **Custom Images**: Use `/local/images/my-event.jpg` for your own images
2. **Auto-generated Icons**: 
   - **Trip**: Blue airplane icon
   - **Milestone**: Red flag
   - **Anniversary**: Pink heart
   - **Special Event**: Purple star icon
3. **Supported Formats**: JPEG, PNG, WebP, GIF, SVG

Images are stored in Home Assistant's `www/` directory and referenced via `/local/` paths.

### Countdown Breakdown Attributes

The `event_date` sensor provides breakdown attributes for building localized countdown text:
- `breakdown_years` - Years component (integer)
- `breakdown_months` - Months component (integer)
- `breakdown_weeks` - Weeks component (integer)
- `breakdown_days` - Days component (integer)

These values are calculated using approximations (365 days/year, 30 days/month) for consistent results. Use these attributes in Lovelace cards or templates to create formatted countdown text in your preferred language.

### Options Flow

All event configurations can be edited after initial setup via the **Options Flow**:

1. Go to **Settings** → **Devices & Services** → **WhenHub**
2. Click **Configure** on the desired event
3. Modify the settings for the respective event (Trip, Milestone, or Anniversary) and save

**Note:** Converting between event types (e.g., Trip to Anniversary) is not possible.

All sensors are automatically updated with the new data.

## Technical Details

| Property | Value |
|----------|-------|
| Update Interval | Once per day (at midnight) |
| IoT Class | `calculated` |
| Platforms | Sensor, Binary Sensor, Image, Calendar |
| Config Flow | Full UI configuration |

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
