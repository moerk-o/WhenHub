### ✨ New Features

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

### ⚠️ Breaking Changes

- **Entity IDs are now standardized to English keys** ([#14](https://github.com/moerk-o/WhenHub/issues/14))

  **All entity IDs are automatically renamed on first startup after the update.** No manual action is required for the migration itself, but you must update any references in dashboards, automations, and scripts before or after the update.

  Entity IDs now always use the internal English type key as their suffix, regardless of the Home Assistant system language. Previously, entity IDs were generated from the translated display name — causing them to differ between language settings.

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

### 📝 Documentation

- Updated README and Technical Reference with upload limits, corrected image storage description, and migration details
- For the complete v2.x.x release history, see [RELEASENOTES_v2.md](RELEASENOTES_v2.md)

**Full Changelog**: https://github.com/moerk-o/WhenHub/compare/v2.3.0...v3.0.0

---
