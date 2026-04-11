#!/bin/bash

#node test_vines.js > test_vines.txt && cat test_vines.txt && rm test_vines.txt

NODE_OPTIONS="--no-warnings" node test_vines.js > test_vines.txt && cat test_vines.txt && rm test_vines.txt