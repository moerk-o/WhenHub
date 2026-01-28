# FR07: Verbesserte Testabdeckung

## Problem

Während der Implementierung von FR04 (Entfernung astronomischer Events) wurde festgestellt, dass keine spezifischen Tests für Special Events existieren. Die 173 vorhandenen Tests liefen nach dem Entfernen der 4 astronomischen Events ohne Änderung durch.

## Betroffene Bereiche

| Bereich | Aktuelle Testabdeckung |
|---------|------------------------|
| Trip Sensors | Gut getestet |
| Milestone Sensors | Gut getestet |
| Anniversary Sensors | Gut getestet |
| Special Events | **Lückenhaft** |
| DST Events | **Unklar** |
| Config Flow | Teilweise |

## Empfohlene Tests

### Special Events
- [ ] Test für jeden Special Event Typ (christmas_eve, easter, etc.)
- [ ] Test für berechnete Events (Easter, Pentecost, Advent)
- [ ] Test für fixe Events (Christmas, Halloween, etc.)
- [ ] Test dass nur gültige special_type Werte akzeptiert werden

### DST Events
- [ ] Test für alle Regionen (EU, USA, Australia, New Zealand)
- [ ] Test für alle DST-Typen (next_change, next_summer, next_winter)
- [ ] Test für is_dst_active Binary Sensor

### Config Flow
- [ ] Test für Special Event Kategorie-Auswahl
- [ ] Test für DST Region/Typ Auswahl

## Priorität

**Niedrig** - Die Integration funktioniert, aber bessere Tests würden zukünftige Änderungen sicherer machen.

## Notizen

Entdeckt bei: FR04 Implementation (2026-01-28)
