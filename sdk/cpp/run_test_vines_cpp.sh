#!/bin/bash

g++ -std=c++17 test_vines.cpp -lz -o test_vines && ./test_vines && rm -f test_vines