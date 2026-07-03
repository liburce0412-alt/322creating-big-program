# Makefile for campus3ai C modules
CC = gcc
CFLAGS = -Wall -O2
OBJ = main.o linked_list.o stack.o queue.o kmp.o hash_table.o binary_search.o

all: main

main: $(OBJ)
	$(CC) $(CFLAGS) -o main $(OBJ)

main.o: main.c
	$(CC) $(CFLAGS) -c main.c

linked_list.o: linked_list.c linked_list.h
	$(CC) $(CFLAGS) -c linked_list.c

stack.o: stack.c stack.h
	$(CC) $(CFLAGS) -c stack.c

queue.o: queue.c queue.h
	$(CC) $(CFLAGS) -c queue.c

kmp.o: kmp.c kmp.h
	$(CC) $(CFLAGS) -c kmp.c

hash_table.o: hash_table.c hash_table.h
	$(CC) $(CFLAGS) -c hash_table.c

binary_search.o: binary_search.c binary_search.h
	$(CC) $(CFLAGS) -c binary_search.c

clean:
	rm -f *.o main main.exe
