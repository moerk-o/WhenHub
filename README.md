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
**Special Event** - Predefined holidays like Christmas, Easter, or DST changes  

## Installation

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

- **Event Name**: e.g., "Denmark Vacation" or "Grandmas visit"
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

- **Event Name**: e.g., "New car delivery" or "Project Deadline"
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

- **Event Name**: e.g., "Birthday Jon" or "Company Anniversary"
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

- **Event Category**: Choose from 3 categories (Traditional Holidays, Calendar Holidays, Daylight Saving Time)
- **Event Name**: e.g., "Christmas Countdown" or "Easter Countdown"
- **Special Event Type**: Choose from 13 predefined holidays
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

Special Events are organized into 3 categories:

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
| Platforms | Sensor, Binary Sensor, Image |
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
