all: base_design

base_design : create_folder Mirage Maya_6BaseWays Mirage_SSL_LocalRandom

#-------------------------
# DEFINES
#-------------------------
CC=g++
CFLAGS=-std=c++0x -O3 

create_folder:
	mkdir -p  bin

#-------------------------
# BINARIES
#-------------------------
Mirage : src/security_mirage.cpp src/mtrand.h
	$(CC) $(CFLAGS) src/security_mirage.cpp -o bin/mirage.o

Maya_6BaseWays : src/security_maya.cpp src/mtrand.h
	$(CC) $(CFLAGS) src/security_maya.cpp -o bin/maya6Ways.o 

Mirage_SSL_LocalRandom : src/bucketsNballs_SSL_LocalRandom_NBn.cpp src/mtrand.h
	$(CC) $(CFLAGS) src/bucketsNballs_SSL_LocalRandom_NBn.cpp -o bin/mirage_ssl_local_random.o

clean:
	rm -rf bin/*.o ; 
