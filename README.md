# Towards Robustness and Realism in Traffic Signal Control

[TODO: short description]


## Installation

1. Clone this repository.

2. [Install CityFlower](https://github.com/ChaseDVickery/CityFlower).
The supported way is through building a Docker image:
```bash
git clone git@github.com:ChaseDVickery/CityFlower.git
cd CityFlower
docker build -t cityflower .
docker run -it -v /path/to/TSC-RR:/src cityflower:latest
```
Check that the installation worked:
```bash
python3 -c "import cityflow"
```

3. Install project dependencies:
```bash
pip install -r requirements.txt
```

4. Download the required data via:
```bash
cd /src
./get-data.sh
```


## Usage

Run `driver.py`.
This should produce replay files for each subdirectory inside of `data`.
These can be viewed using CityFlow's frontend.
