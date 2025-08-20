#!/bin/bash

# Check for required arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <config_url> <test_url>"
    exit 1
fi

CONFIG_URL=$1
TEST_URL=$2

# Download and prepare LiteSpeedTest
wget -O lite-linux-amd64.gz https://github.com/xxf098/LiteSpeedTest/releases/download/v0.15.0/lite-linux-amd64-v0.15.0.gz
gzip -d lite-linux-amd64.gz
wget -O lite_config.json "$CONFIG_URL"

# Run LiteSpeedTest
chmod +x ./lite-linux-amd64
sudo nohup ./lite-linux-amd64 --config ./lite_config.json --test "$TEST_URL" > speedtest.log 2>&1 &
