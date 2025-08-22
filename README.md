# WhenHub

![Version](https://img.shields.io/badge/version-1.3.0-blue.svg)
![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.1+-green.svg)

WhenHub is a Home Assistant integration for tracking various events and important dates. The integration provides countdown sensors, status information, and visual representations for your events.

## Overview

**The origin story:** The kids kept asking "How much longer until vacation?" or "How many days until my birthday?". I thought, there's got to be something I can do with Home Assistant! Now WhenHub displays an image of the event on the tablet with a big number showing the remaining days and the duration as text below.

### Event Types

**Trip** - Multi-day events like vacations or visiting grandma  
**Milestone** - One-time important dates like school events or 'when is the new pet coming'  
**Anniversary** - Yearly recurring events like birthdays or holidays  
**Special Event** - Predefined holidays and astronomical events like Christmas, Easter, or Solstices  

## Installation

### Manual Installation

1. Download the latest version from the [Releases page](https://github.com/yourusername/whenhub/releases)
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
- **Website URL** *(optional)*: Link to accommodation or other relevant info
- **Notes** *(optional)*: Additional information

### Available Entities

#### Sensors
- **Countdown Text** - Formatted countdown text, will stay at 0 once the date has passed
  - **Attributes**: 
    - `event_name` - Name of the event
    - `event_type` - Type of event (trip)
    - `start_date` - Start date (ISO format)
    - `end_date` - End date (ISO format)
    - `total_days` - Total trip duration in days
    - `text_years` - Years from countdown text until start
    - `text_months` - Months from countdown text until start
    - `text_weeks` - Weeks from countdown text until start
    - `text_days` - Days from countdown text until start
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
- **Website URL** *(optional)*: Relevant URL for the event
- **Notes** *(optional)*: Additional information

### Available Entities

#### Sensors
- **Countdown Text** - Formatted countdown text, will stay at 0 once the date has passed
  - **Attributes**: 
    - `event_name` - Name of the event
    - `event_type` - Type of event (milestone)
    - `date` - Target date (ISO format)
    - `text_years` - Years from countdown text until target
    - `text_months` - Months from countdown text until target
    - `text_weeks` - Weeks from countdown text until target
    - `text_days` - Days from countdown text until target
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
- **Website URL** *(optional)*: Relevant URL for the event
- **Notes** *(optional)*: Additional information

### Available Entities

#### Sensors
- **Countdown Text** - Formatted countdown text to next anniversary, will show 0 only on anniversary day
  - **Attributes**: 
    - `event_name` - Name of the event
    - `event_type` - Type of event (anniversary)
    - `initial_date` - Original date (ISO format)
    - `next_anniversary` - Date of next anniversary (ISO format)
    - `years_on_next` - Number of years at next anniversary
    - `text_years` - Years from countdown text until next anniversary
    - `text_months` - Months from countdown text until next anniversary
    - `text_weeks` - Weeks from countdown text until next anniversary
    - `text_days` - Days from countdown text until next anniversary
- **Days Until Next** - Days until next anniversary
- **Days Since Last** - Days since last anniversary
- **Occurrences Count** - Number of past occurrences
- **Next Date** - Date of next anniversary (ISO format)
- **Last Date** - Date of last anniversary (ISO format)

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

Special events track holidays and astronomical events that repeat annually. These include both fixed-date holidays and calculated events with complex date algorithms.

### Configuration

When setting up a Special Event, you configure:

- **Event Category**: Choose from 3 categories (Traditional Holidays, Calendar Holidays, Astronomical Events)
- **Event Name**: e.g., "Weihnachts-Countdown" or "Oster-Countdown"
- **Special Event Type**: Choose from 17 predefined holidays and astronomical events
- **Image Path** *(optional)*: 
  - Leave empty = Automatically generated default image (purple star icon)
  - File path = e.g., `/local/images/christmas.jpg` for custom images
  - Base64 string = Directly embedded encoded image
- **Website URL** *(optional)*: Relevant URL for the event
- **Notes** *(optional)*: Additional information

### Available Entities

#### Sensors
- **Days Until** - Days until next occurrence
- **Days Since Last** - Days since last occurrence
- **Countdown Text** - Formatted countdown text to next occurrence
  - **Attributes**: 
    - `event_name` - Name of the event
    - `event_type` - Type of event (special)
    - `special_type` - Specific holiday type (e.g., "christmas", "easter")
    - `special_name` - Display name of the holiday
    - `next_date` - Date of next occurrence
    - `text_years` - Years from countdown text until next
    - `text_months` - Months from countdown text until next
    - `text_weeks` - Weeks from countdown text until next
    - `text_days` - Days from countdown text until next
- **Next Date** - ISO date of next occurrence
- **Last Date** - ISO date of last occurrence

#### Binary Sensors
- **Is Today** - `true` when today is the special event day

#### Image
- **Event Image** - Shows the configured image or default purple star icon
  - **Attributes**: 
    - `image_type` - "user_defined" (custom image) or "system_defined" (default icon)
    - `image_path` - Path to image, "base64_data" or "default_svg"

### Available Special Events

Special Events are organized into 3 categories with a total of 17 events:

#### Traditional Holidays (11 Events)
Fixed and calculated events celebrating traditional holidays:

**Fixed Date Events:**
- **Heilig Abend** - December 24th (Christmas Eve)
- **1. Weihnachtstag** - December 25th (Christmas Day)
- **2. Weihnachtstag** - December 26th (Boxing Day)
- **Halloween** - October 31st
- **Nikolaus** - December 6th (St. Nicholas Day)

**Calculated Events using the Gauss Easter Algorithm:**
- **Ostersonntag** - Easter Sunday (base calculation)
- **Pfingstsonntag** - 49 days after Easter (Pentecost Sunday)

**Advent Sundays (calculated from Christmas Eve):**
- **1. Advent** - 4th Sunday before Christmas Eve
- **2. Advent** - 3rd Sunday before Christmas Eve  
- **3. Advent** - 2nd Sunday before Christmas Eve
- **4. Advent** - Sunday before Christmas Eve

#### Calendar Holidays (2 Events)
Fixed calendar events marking year transitions:
- **Neujahr** - January 1st (New Year's Day)
- **Silvester** - December 31st (New Year's Eve)

#### Astronomical Events (4 Events)
Fixed dates for seasonal transitions:
- **Frühlingsanfang** - March 20th (Spring Equinox)
- **Sommeranfang** - June 21st (Summer Solstice)
- **Herbstanfang** - September 23rd (Autumn Equinox)  
- **Winteranfang** - December 21st (Winter Solstice)

*Note: Astronomical events use simplified approximations. Actual dates may vary by ±1 day due to Earth's orbital mechanics.*

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

#### Astronomical Events
Astronomical events use fixed dates for consistent scheduling:
- Spring Equinox: March 20th
- Summer Solstice: June 21st  
- Autumn Equinox: September 23rd
- Winter Solstice: December 21st

These are simplified approximations for seasonal planning. For precise astronomical calculations, consider using specialized astronomy integrations.

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

### Countdown Text Formatting

The countdown text uses intelligent German formatting
*(multilingual support coming soon):*
- **Complete**: "2 Jahre, 3 Monate, 1 Woche, 4 Tage"
- **Shortened**: "5 Tage" (zero values are omitted)
- **Reached**: "0 Tage" when the date is reached or passed

The calculation uses approximations (365 days/year, 30 days/month) for consistent results.

### Options Flow

All event configurations can be edited after initial setup via the **Options Flow**:

1. Go to **Settings** → **Devices & Services** → **WhenHub**
2. Click **Configure** on the desired event
3. Modify the settings for the respective event (Trip, Milestone, or Anniversary) and save

**Note:** Converting between event types (e.g., Trip to Anniversary) is not possible.

All sensors are automatically updated with the new data.

## Contributors Welcome

This project is open source and contributions are warmly welcomed! Issues for bugs or feature requests are just as appreciated as pull requests for code improvements.

---

⭐ **Like WhenHub?** Instead of buying me a coffee, give the project a star on GitHub!
