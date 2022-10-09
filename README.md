# Towards Robustness and Realism in Traffic Signal Control

[TODO: short description]


## Installation

1. Clone this repository.

2. [Install CityFlow](https://cityflow.readthedocs.io/en/latest/install.html).
The supported way is through their pre-made Docker image:
```bash
docker pull cityflowproject/cityflow:latest
docker run -it -v /path/to/TSC-RR:/src cityflowproject/cityflow:latest
```
Check that the installation worked:
```bash
python3 -c "import cityflow"
```

3. Download the required data via:
```bash
cd /src
./get-data.sh
```


## Usage

Run `driver.py`.
This should produce replay files for each subdirectory inside of `data`.
These can be viewed using CityFlow's frontend.