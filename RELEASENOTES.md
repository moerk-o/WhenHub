### 💣 Breaking Changes

- **Entity IDs are now standardized to English keys** ([#14](https://github.com/moerk-o/WhenHub/issues/14))

  A common use case for WhenHub is building reusable dashboard cards and automations — a card that shows the countdown for any trip, or an automation that triggers when any anniversary is today. To make this work, you need to be able to predict the entity IDs without looking them up first.

  That was not reliably possible before: entity IDs were generated from the translated sensor name, so the same sensor had different IDs depending on the Home Assistant system language. On a German installation, the event date sensor was called `sensor.mein_urlaub_ereignisdatum` — on an English one, `sensor.my_vacation_event_date`. Sharing a dashboard card or automation between two HA instances simply did not work without manual adjustments.

  **Starting with v3.0.0, entity IDs always use a fixed English type key as their suffix**, regardless of the HA language setting. A sensor that was `ereignisdatum` on German is now `event_date` everywhere. This makes entity IDs predictable, shareable, and template-friendly.

  **Migration: all entity IDs are automatically renamed on first startup after the update.** No manual action is required for the migration itself — but if you have existing dashboards, automations, or scripts that reference WhenHub entity IDs, **you will need to update those references.**

  **Affected suffixes (all installations):**

  | Old suffix | New suffix |
  |---|---|
  | `days_until_start` | `days_until` |
  | `trip_days_remaining` | `trip_left_days` |
  | `trip_percent_remaining` | `trip_left_percent` |
  | `daylight_saving_time_active` | `is_dst_active` |

  **Additional suffixes affected on non-English Home Assistant installations** (e.g. German): all entity ID suffixes were previously in the system language and are now standardized to English.

  **Example (German installation):**
  - Before: `sensor.johns_geburtstag_ereignisdatum`
  - After: `sensor.johns_geburtstag_event_date`

### ✨ New Features

- **Entity as date source** ([#9](https://github.com/moerk-o/WhenHub/issues/9))
  - Trip, Milestone, and Anniversary events can now use a Home Assistant entity (`device_class: date` or `timestamp`) as their date source instead of a fixed date
  - Enable per date field via the toggle next to the date input in the config/options flow
  - The coordinator reads the entity state on every update — date changes are reflected immediately
  - When an entity source is active, the **Event Date** sensor shows a different icon (`mdi:calendar-sync`) and exposes the source entity ID as an attribute


- **Expiry Notifications** ([#13](https://github.com/moerk-o/WhenHub/issues/13))
  - Trip, Milestone, and Custom Pattern events can now notify you when they expire
  - An actionable issue appears in **Settings → System → Repairs** with a one-click removal flow
  - Enable per event via the "Notify when expired" toggle (off by default)
  - Auto-resolves if you update the event dates so it is no longer expired

### 🐞 Bug Fixes

- **Image upload validation** ([#12](https://github.com/moerk-o/WhenHub/issues/12))
  - Uploaded files are now validated server-side: only JPEG, PNG, WebP and GIF are accepted
  - Files larger than 5 MB are rejected with a clear error message
  - Options flow now shows translated error messages (previously displayed raw error keys)


### 📝 Documentation

- For the complete v2.x.x release history, see [RELEASENOTES_v2.md](RELEASENOTES_v2.md)

**Full Changelog**: https://github.com/moerk-o/WhenHub/compare/v2.3.0...v3.0.0

---
