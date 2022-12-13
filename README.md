# Towards Robustness and Realism in Traffic Signal Control

Term project for [CS5834](https://cs.vt.edu/Graduate/Courses/GradCourseDescriptions.html#CS5834).
Introduces additional features to the [CityFlow](https://github.com/cityflow-project/CityFlow) simulation that more accurately model real-world situations:

* Variable number of passengers in each vehicle
  * Metrics updated to account for each person's travel/wait times
  * Allows prioritizing high-occupancy vehicles such as buses
* Pedestrians and sidewalks
  * Allows developing algorithms friendly to every type of commuter


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

To reproduce results shown in the report, use `./run-all.sh`.
