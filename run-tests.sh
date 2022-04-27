#!/bin/sh -e
# Check if virtualenv is available and if it is use it
if command -v virtualenv; then
  # Create a virtual venv in order not to pollute
  # the main python libs if the venv already
  # exist no harm is done
  virtualenv -p python3 venv
  . venv/bin/activate
  # install requirements
  python3 -m pip install -r requirements.txt
  python3 -m pip install -r dev_requirements.txt
  # Execute pytest and pass along the arguments
  # used to call this script
  pytest $@
else
  echo "virtualenv not installed"
  # Execute pytest and pass along the arguments
  # used to call this script
  pytest $@
fi
