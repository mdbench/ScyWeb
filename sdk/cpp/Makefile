# Makefile for ScyWeb C++ Kernel Test
CXX = g++
CXXFLAGS = -std=c++17 -Wall
LIBS = -lcrypto

all: test_vines

test_vines: test_vines.cpp
	$(CXX) $(CXXFLAGS) test_vines.cpp -o test_vines $(LIBS)

clean:
	rm -f test_vines