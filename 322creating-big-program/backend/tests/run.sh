#!/bin/bash
echo "========== CampusAI Smoke Tests =========="
cd "$(dirname "$0")"
python3 smoke_test.py
echo ""
if [ $? -eq 0 ]; then
    echo "All tests passed!"
else
    echo "Some tests failed!"
fi