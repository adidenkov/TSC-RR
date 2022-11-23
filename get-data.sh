#!/usr/bin/env bash
# Create a data directory and populate with datasets.
SRC=$(pwd)
mkdir -p data
cd data
dl () { wget -nc -O $1 https://raw.githubusercontent.com/$2; }
up () { python3 $SRC/scripts/add_passengers_to_flow.py $1/flow.json -o $1/flow.json; }

# Small example from CityFlow
mkdir -p 1-example
dl 1-example/roadnet.json cityflow-project/CityFlow/master/examples/roadnet.json
dl 1-example/flow.json cityflow-project/CityFlow/master/examples/flow.json
up 1-example

# Based on camera data in Hangzhou
mkdir -p 1-hangzhou
dl 1-hangzhou/roadnet.json traffic-signal-control/sample-code/master/data/hangzhou_1x1_bc-tyc_18041607_1h/roadnet.json
dl 1-hangzhou/flow.json traffic-signal-control/sample-code/master/data/hangzhou_1x1_bc-tyc_18041607_1h/flow.json
up 1-hangzhou

# Synthetic grid and patterns
mkdir -p 3-gaussian
dl 3-gaussian/roadnet.json traffic-signal-control/sample-code/master/data/syn_1x3_gaussian_500_1h/roadnet_1X3.json
dl 3-gaussian/flow.json traffic-signal-control/sample-code/master/data/syn_1x3_gaussian_500_1h/syn_1x3_gaussian_500_1h.json
up 3-gaussian

# Based on camera data in Jinan
mkdir -p 12-jinan
dl 12-jinan/roadnet.json wingsweihua/colight/master/data/Jinan/3_4/roadnet_3_4.json
dl 12-jinan/flow.json wingsweihua/colight/master/data/Jinan/3_4/anon_3_4_jinan_real.json
up 12-jinan

# Generated from taxicab trajectories
mkdir -p 48-manhattan
dl 48-manhattan/roadnet.json traffic-signal-control/sample-code/master/data/manhattan_16x3/roadnet_16_3.json
dl 48-manhattan/flow.json traffic-signal-control/sample-code/master/data/manhattan_16x3/anon_16_3_newyork_real.json
up 48-manhattan

mkdir -p 196-manhattan
dl 196-manhattan/roadnet.json traffic-signal-control/sample-code/master/data/manhattan_28x7/roadnet_28_7.json
dl 196-manhattan/flow.json traffic-signal-control/sample-code/master/data/manhattan_28x7/anon_28_7_newyork_real_triple.json
up 196-manhattan

mkdir -p 2510-manhattan
dl 2510-manhattan/roadnet.json Chacha-Chen/MPLight/master/data/manhattan/manhattan.json
dl 2510-manhattan/flow.json Chacha-Chen/MPLight/master/data/manhattan/manhattan_31217.json
up 2510-manhattan
