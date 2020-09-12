<img src="https://drive.google.com/uc?id=1DbOz3wWzPobyg11mDMITEp5FIcfRnZTw" height=50px />

# SUMO Server
Server for simulating traffic and relaying traffic information programatically through SUMO.

### Installation
This project requires Python 3.8+ and an existing [SUMO installation](https://sumo.dlr.de/docs/Downloads.php) with Python bindings and `sumo-tools`.

#### Development
1. Clone this repository:
```bash
git clone git@github.com:muve-traffic/sumo-server.git
```

2. Change directory into the cloned repository's directory:
```bash
cd sumo-server
```

3. Configure the installation:
```bash
./configure.sh
```
This checks for the existence of a SUMO installation with Python bindings, creates a Python virtual environment, and installs in the SUMO Python packages to the environment.

4. Source into the created virtual environment:
```bash
source .venv/bin/activate
```

5. Install the simulation server in development mode with all linting and testing requirements:
```bash
pip install -e '.[lint, test, tox]'
```

6. Test that everything works correctly:
```bash
tox -p --sitepackages
```
