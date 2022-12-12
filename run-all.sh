#!/usr/bin/env bash

# Busses
echo && echo "=== Bus simulations ==="
echo "Default:" && ./driver.py --bus -i results_bus-default.json -o results_bus-default.json
# TODO: Max-P
# TODO: W-Max-P

# Pedestrians
echo && echo "=== Pedestrian simulations ==="
echo "Default:" && ./driver.py --pedestrian -i results_pedestrian-default.json -o results_pedestrian-default.json
# TODO: Unsynced
# TODO: Cars
# TODO: Cars+Peds