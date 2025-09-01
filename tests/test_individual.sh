#!/bin/bash
# Schneller Test-Ausführer für einzelne Tests per Nummer
# 
# Usage:
#   ./test_individual.sh 17
#   ./test_individual.sh 1 5 42
#   ./test_individual.sh --list
#   ./test_individual.sh --category trip

cd "$(dirname "$0")"
python3 run_test.py "$@"