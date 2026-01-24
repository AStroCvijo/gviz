#!/bin/bash

# Initialize conda properly
eval "$(conda shell.bash hook)"

# Create and activate conda env
conda create --name gviz python=3.9 -y
conda activate gviz

# Install dependencies
pip install -r requirements.txt

# Go to app
cd gviz/

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver