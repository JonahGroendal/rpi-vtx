#!/bin/bash

ffplay -fflags nobuffer -flags low_delay -vf setpts=0 udp://rpi4cam.local:10001
