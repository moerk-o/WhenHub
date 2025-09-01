#!/usr/bin/env python3
"""
Test Execution Helper für WhenHub Tests

Ermöglicht das Ausführen einzelner Tests per Nummer aus dem KATALOG.md.

Usage:
    python run_test.py 17                    # Test 17 ausführen
    python run_test.py 1 5 42               # Tests 1, 5 und 42 ausführen
    python run_test.py --list               # Alle verfügbaren Tests auflisten
    python run_test.py --category trip      # Alle Trip-Tests ausführen
"""

import sys
import subprocess
import re
from pathlib import Path

# Test-Katalog aus KATALOG.md laden
def load_test_catalog():
    """Lädt den Test-Katalog aus KATALOG.md."""
    katalog_path = Path(__file__).parent.parent / "KATALOG.md"
    
    if not katalog_path.exists():
        print("❌ KATALOG.md nicht gefunden!")
        sys.exit(1)
    
    with open(katalog_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Tabellen-Zeilen extrahieren (Format: | # | Test-Funktion | Datei | Beschreibung |)
    tests = {}
    category_mapping = {}
    current_category = None
    
    lines = content.split('\n')
    for line in lines:
        # Kategorie-Header erkennen
        if line.startswith('### '):
            current_category = line.replace('### ', '').strip()
            continue
            
        # Tabellen-Zeile parsen
        if line.startswith('| ') and ' | ' in line and not line.startswith('|---'):
            parts = [p.strip() for p in line.split('|')[1:-1]]  # Erste und letzte sind leer
            if len(parts) >= 4 and parts[0].isdigit():
                test_num = int(parts[0])
                test_func = parts[1].strip('`')
                test_file = parts[2]
                description = parts[3]
                
                tests[test_num] = {
                    'function': test_func,
                    'file': test_file,
                    'description': description,
                    'category': current_category
                }
                category_mapping[test_num] = current_category
    
    return tests

def run_single_test(test_num: int, tests: dict):
    """Führt einen einzelnen Test aus."""
    if test_num not in tests:
        print(f"❌ Test {test_num} nicht gefunden!")
        return False
    
    test_info = tests[test_num]
    test_file = test_info['file']
    test_func = test_info['function']
    
    # pytest Kommando zusammenbauen - aus tests/ Verzeichnis
    pytest_target = f"tests/{test_file}::{test_func}"
    
    print(f"🧪 Test {test_num}: {test_info['description']}")
    print(f"📁 Ausführung: pytest -v {pytest_target}")
    print("─" * 80)
    
    # Test ausführen mit aktivierter .venv
    project_root = Path(__file__).parent.parent
    venv_python = project_root / ".venv" / "bin" / "python"
    
    try:
        if venv_python.exists():
            # Verwende das Python aus der .venv
            result = subprocess.run([
                str(venv_python), "-m", "pytest", 
                "-v", pytest_target,
                "--tb=short"  # Kürzere Tracebacks
            ], cwd=project_root, capture_output=False)
        else:
            # Fallback auf system python
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "-v", pytest_target,
                "--tb=short"
            ], cwd=project_root, capture_output=False)
        
        if result.returncode == 0:
            print(f"✅ Test {test_num} erfolgreich!")
            return True
        else:
            print(f"❌ Test {test_num} fehlgeschlagen!")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Ausführen von Test {test_num}: {e}")
        return False

def list_tests(tests: dict, category_filter: str = None):
    """Listet alle Tests auf."""
    if category_filter:
        filtered_tests = {k: v for k, v in tests.items() 
                         if v['category'] and category_filter.lower() in v['category'].lower()}
        print(f"📋 Tests in Kategorie '{category_filter}':")
    else:
        filtered_tests = tests
        print("📋 Alle verfügbaren Tests:")
    
    print("─" * 100)
    
    current_category = None
    for test_num in sorted(filtered_tests.keys()):
        test_info = filtered_tests[test_num]
        
        # Kategorie-Header anzeigen
        if test_info['category'] != current_category:
            current_category = test_info['category']
            if current_category:
                print(f"\n🏷️  {current_category}")
                print("─" * 50)
        
        print(f"{test_num:3d} | {test_info['function']:<40} | {test_info['description']}")
    
    print("─" * 100)
    print(f"Total: {len(filtered_tests)} Tests")

def main():
    """Hauptfunktion."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    # Test-Katalog laden
    tests = load_test_catalog()
    
    args = sys.argv[1:]
    
    # Kommandos verarbeiten
    if args[0] == '--list':
        list_tests(tests)
        return
    
    if args[0] == '--category' and len(args) > 1:
        list_tests(tests, args[1])
        return
    
    # Test-Nummern verarbeiten
    test_numbers = []
    for arg in args:
        try:
            test_numbers.append(int(arg))
        except ValueError:
            print(f"❌ Ungültige Test-Nummer: {arg}")
            sys.exit(1)
    
    # Tests ausführen
    success_count = 0
    total_count = len(test_numbers)
    
    for test_num in test_numbers:
        if run_single_test(test_num, tests):
            success_count += 1
        print()  # Leerzeile zwischen Tests
    
    # Zusammenfassung
    if total_count > 1:
        print("═" * 80)
        print(f"📊 Zusammenfassung: {success_count}/{total_count} Tests erfolgreich")
        if success_count == total_count:
            print("🎉 Alle Tests bestanden!")
        else:
            print(f"⚠️  {total_count - success_count} Test(s) fehlgeschlagen")

if __name__ == "__main__":
    main()