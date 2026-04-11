#!/bin/bash

kotlinc ScyKernel.kt test_vines.kt -include-runtime -d test_vines.jar && \
java -jar test_vines.jar > test_vines.txt && \
cat test_vines.txt && \
rm test_vines.txt