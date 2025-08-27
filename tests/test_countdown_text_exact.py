"""Tests für exakte Countdown-Text Formatierung bei spezifischen Zeitspannen."""
import pytest
from homeassistant.core import HomeAssistant
from _helpers import at, setup_and_wait, get_state


@pytest.mark.asyncio
async def test_countdown_text_exact_two_weeks(hass: HomeAssistant, trip_config_entry):
    """
    Test für strikte 14-Tage-Text Formatierung: Exakt "2 Wochen", nicht "14 Tage".
    
    Warum:
      Bei exakt 14 Tagen sollte der Countdown-Text die strukturierte Form "2 Wochen"
      verwenden statt der dezimalen "14 Tage" Darstellung. Dies ist nutzerfreundlicher
      und zeigt die hierarchische Zeitformatierung der Integration.
      
    Wie:
      Trip "Dänemark 2026" (Start: 2026-07-12, Ende: 2026-07-26).
      Zeitpunkt: Exakt 14 Tage vor Start (2026-06-28 10:00:00 UTC).
      Prüfung des countdown_text Sensors auf exakte "2 Wochen" Formulierung.
      
    Erwartung:
      - countdown_text enthält "2 Wochen"
      - countdown_text enthält NICHT "14 Tage"
      - Strikte Formatierung ohne Alternative/Toleranz
    """
    # Exakt 14 Tage vor Trip-Start (2026-07-12 minus 14 Tage = 2026-06-28)
    with at("2026-06-28 10:00:00+00:00"):
        await setup_and_wait(hass, trip_config_entry)
        
        # Prüfe countdown_text für strukturierte Wochenformatierung
        countdown_text = get_state(hass, "sensor.danemark_2026_countdown_text")
        countdown_value = countdown_text.state
        
        # Strikte Anforderungen: "2 Wochen" statt "14 Tage"
        assert "2 Wochen" in countdown_value, f"Expected '2 Wochen' in countdown text, got: {countdown_value}"
        assert "14 Tage" not in countdown_value, f"Should NOT contain '14 Tage', got: {countdown_value}"
        
        # Zusätzliche Validierung: Text sollte nicht leer sein
        assert len(countdown_value) > 0, "Countdown text should not be empty"
        
        # Dokumentation der IST-Semantik für 14-Tage-Fall
        print(f"✅ IST-Verhalten 14 Tage vorher: '{countdown_value}'")