### ✨ New Features

- **WhenHub Calendar**
  - All your WhenHub events are now available as a native Home Assistant calendar — visible in the calendar card and queryable in automations
  - Create multiple independent calendars with different scopes: show everything, filter by event type (e.g. only Trips), or pick individual entries

- **Repeating Events**
  - New event type for anything that follows a regular pattern: weekly team meetings, monthly bill reminders, annual traditions
  - Choose from daily, weekly (select individual weekdays), monthly, or yearly; optionally set an end date or a maximum occurrence count

- **Event Images**
  - Give every event its own image — drag and drop a photo directly in the setup dialog
  - The image appears as a dedicated entity in the image platform, ready to use on dashboards

- **URL and Memo**
  - Attach a booking link or free-text notes to any event — useful for holidays, trips, or project milestones
  - Both appear as Home Assistant sensors the moment the field is filled in, making them available to automations and companion apps

### 🐞 Bug Fixes

- **Cleaner Setup Flow**: The event name field no longer appears twice; WhenHub now generates a sensible title automatically and increments it if a duplicate already exists (e.g. "Trip 2")
- **Next Date Sensor**: Fixed an off-by-one where the "next date" showed today on days the pattern fires, instead of pointing to the following occurrence

**Full Changelog**: https://github.com/moerk-o/WhenHub/compare/v2.2.2...v2.3.0

---

# v2.2.2

### 🐞 Bug Fixes

- **Binary Sensor Display Fixed**: Binary sensors now show "On/Off"

- **DST Default Name Localization**: Removed hardcoded German default names for DST events

**Full Changelog**: https://github.com/moerk-o/WhenHub/compare/v2.2.1...v2.2.2

---

# v2.2.1

### ✨ New Features

- **Language-based Entity IDs**
  - Entity IDs now based on configured HA language
  - Correct translations for sensor names in DE/EN
  - `EntityDescription` for consistent naming

- **Improved Date Picker**
  - Native Home Assistant `DateSelector` for date selection
  - Better UX in Config Flow

### 🐞 Bug Fixes
- **OptionsFlow Error Fixed**: 500 Internal Server Error when clicking "Configure" in newer Home Assistant versions
  - Cause: `config_entry` is a read-only property of `OptionsFlow` base class in newer HA versions
  - Fix: Removed `__init__` method from `OptionsFlowHandler`
- **DSTBinarySensor Icon Bug**: Fixed `AttributeError` when accessing `_attr_icon`
- **Options Flow Error Display**: Validation errors are now displayed correctly

### 🔧 Infrastructure
- **Device Info Cleanup**: Removed firmware version from device info (WhenHub events are virtual devices without actual firmware)
- **HACS ZIP Release**: Enabled `zip_release` 

### 📝 Documentation
- Added GitHub repository description and topics

### 🗑️ Removed
- **Astronomical Events Removed**
  - Sunrise, sunset, solstice, equinox removed
  - These are better covered by dedicated integrations (e.g., [Solstice Season](https://github.com/moerk-o/ha-solstice_season) for precise seasonal data or HA Core [Sun](https://www.home-assistant.io/integrations/sun/))

**Full Changelog**: https://github.com/moerk-o/WhenHub/compare/v2.2.0...v2.2.1

---

# v2.2.0 (internal)

*This version was released but superseded by v2.2.1. Changes are included above.*

---

# v2.1.0 (internal)

*This version was not released publicly. Changes are included in v2.2.1.*

---

# v2.0.0

### ✨ New Features
- **Internationalization**
  - Full German and English support
  - UI automatically adapts to your Home Assistant language setting

- **Localized Date Display**
  - Date sensors now show relative time in the frontend ("In 18 days", "Tomorrow")
  - Use `format: relative`, `format: date`, etc. in Lovelace cards

- **Improved Sensor Classes**
  - `device_class: timestamp` for all date sensors
  - `device_class: duration` with unit "d" for all days sensors

### 📝 Documentation
- Updated README with new features documentation

### 🔧 Infrastructure
- Code cleanup and improved type hints

**Full Changelog**: https://github.com/moerk-o/WhenHub/compare/v1.0.0...v2.0.0
