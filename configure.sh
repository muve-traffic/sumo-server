#!/bin/sh

# SUMO Python packages that we want to install
readonly SUMO_DEPS=( "libsumo" "traci" "sumolib" )

# Check if each SUMO package is properly installed and get the path to it
echo "Looking for SUMO Python packages: " ${SUMO_DEPS[@]}
SUMO_PKGS=()
for dep in ${SUMO_DEPS[@]}; do
  init=$(python -c "import $dep; print($dep.__file__);")
  ret=$?
  if [[ $ret -ne 0 ]]; then
    echo "Could not find $dep. Make sure that SUMO is properly installed with Python bindings and that you are not in a Python virtual environment."
    exit 1
  fi
  lib=$(dirname $init)
  SUMO_PKGS+=( $lib )
done
readonly SUMO_PKGS
echo "Found SUMO Python packages: " ${SUMO_PKGS[@]}


# Create a virtual environment and upgrade pip
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip setuptools wheel

# Link the SUMO packages into this virtual environment
SITE_PKGS=$(python -c "import site; print(site.getsitepackages()[0])")
for pkg in ${SUMO_PKGS[@]}; do
  ln -v -s $pkg* $SITE_PKGS/
done

# Confirm the installation of the SUMO packages into the virtual environment
for dep in ${SUMO_DEPS[@]}; do
  init=$(python -c "import $dep; print($dep.__file__);")
  ret=$?
  if [[ $ret -ne 0 ]]; then
    echo "Something went wrong with the installation of $dep into the virtual environment. Python could not find the package. Check if any other errors were emitted by this script."
    exit 1
  fi
  lib=$(dirname $init)
  echo $lib
done
