all: campus_lib

campus_lib: main.o linked_list.o stack.o queue.o kmp.o hash_table.o binary_search.o
	gcc -Wall -O2 -o campus_lib main.o linked_list.o stack.o queue.o kmp.o hash_table.o binary_search.o

main.o: main.c
	gcc -Wall -O2 -c main.c -o main.o
linked_list.o: linked_list.c linked_list.h
	gcc -Wall -O2 -c linked_list.c -o linked_list.o
stack.o: stack.c stack.h
	gcc -Wall -O2 -c stack.c -o stack.o
queue.o: queue.c queue.h
	gcc -Wall -O2 -c queue.c -o queue.o
kmp.o: kmp.c kmp.h
	gcc -Wall -O2 -c kmp.c -o kmp.o
hash_table.o: hash_table.c hash_table.h
	gcc -Wall -O2 -c hash_table.c -o hash_table.o
binary_search.o: binary_search.c binary_search.h
	gcc -Wall -O2 -c binary_search.c -o binary_search.o

clean:
	rm -f campus_lib *.o
