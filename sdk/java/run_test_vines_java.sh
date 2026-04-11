#!/bin/bash

javac ScyKernel.java test_vines.java && \
stdbuf -o0 java test_vines > test_vines.txt && \
cat test_vines.txt && \
rm test_vines.txt