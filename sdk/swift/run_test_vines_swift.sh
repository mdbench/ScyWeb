#!/bin/bash

swiftc -O ScyKernel.swift test_vines.swift -o test_vines && ./test_vines && rm test_vines