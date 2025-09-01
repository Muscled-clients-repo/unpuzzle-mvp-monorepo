#!/bin/bash

# Backend Django Setup Script
# This script checks for virtual environment and sets up dependencies

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}  Django Backend Setup Script${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}✗ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check if virtual environment exists
VENV_DIR="venv"
if [ -d "$VENV_DIR" ]; then
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
    
    # Check if it's a valid Python virtual environment
    if [ -f "$VENV_DIR/bin/activate" ]; then
        echo -e "${GREEN}✓ Valid virtual environment detected${NC}"
    else
        echo -e "${YELLOW}⚠ Invalid virtual environment found. Creating new one...${NC}"
        rm -rf "$VENV_DIR"
        python3 -m venv "$VENV_DIR"
        echo -e "${GREEN}✓ New virtual environment created${NC}"
    fi
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Virtual environment created successfully${NC}"
    else
        echo -e "${RED}✗ Failed to create virtual environment${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}✗ Failed to activate virtual environment${NC}"
    exit 1
fi

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ pip upgraded successfully${NC}"
else
    echo -e "${YELLOW}⚠ Warning: pip upgrade failed, continuing...${NC}"
fi

# Check which requirements file to use
REQUIREMENTS_FILE=""
if [ -f "requirements.txt" ]; then
    REQUIREMENTS_FILE="requirements.txt"
elif [ -f "requirements/development.txt" ]; then
    REQUIREMENTS_FILE="requirements/development.txt"
elif [ -f "requirements/base.txt" ]; then
    REQUIREMENTS_FILE="requirements/base.txt"
else
    echo -e "${RED}✗ No requirements file found!${NC}"
    echo -e "${YELLOW}  Checked for:${NC}"
    echo -e "${YELLOW}  - requirements.txt${NC}"
    echo -e "${YELLOW}  - requirements/development.txt${NC}"
    echo -e "${YELLOW}  - requirements/base.txt${NC}"
    exit 1
fi

echo -e "${YELLOW}Installing dependencies from $REQUIREMENTS_FILE...${NC}"
pip install -r "$REQUIREMENTS_FILE"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✓ .env file created${NC}"
        echo -e "${YELLOW}  Please update .env with your configuration${NC}"
    else
        echo -e "${YELLOW}⚠ No .env file found. Please create one if needed.${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py migrate
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database migrations completed${NC}"
else
    echo -e "${YELLOW}⚠ Database migration failed. You may need to configure your database settings.${NC}"
fi

# Collect static files (optional, for production)
echo -e "${YELLOW}Would you like to collect static files? (y/n)${NC}"
read -r COLLECT_STATIC
if [[ $COLLECT_STATIC == "y" || $COLLECT_STATIC == "Y" ]]; then
    python manage.py collectstatic --noinput
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Static files collected${NC}"
    else
        echo -e "${YELLOW}⚠ Failed to collect static files${NC}"
    fi
fi

echo ""
echo -e "${GREEN}==================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}==================================${NC}"
echo ""
echo -e "${GREEN}To start the development server:${NC}"
echo -e "${YELLOW}  source venv/bin/activate${NC}"
echo -e "${YELLOW}  python manage.py runserver${NC}"
echo ""
echo -e "${GREEN}To deactivate the virtual environment:${NC}"
echo -e "${YELLOW}  deactivate${NC}"