#!/bin/bash

swiftc -O ScyKernel.swift test_vines.swift -lz -o test_vines && ./test_vines && rm test_vines