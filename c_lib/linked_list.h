#ifndef LINKED_LIST_H
#define LINKED_LIST_H
typedef struct Node { void* data; struct Node* prev; struct Node* next; } Node;
typedef struct { Node* head; Node* tail; int size; } LinkedList;
LinkedList* ll_create();
void ll_append(LinkedList* list, void* data);
void ll_free(LinkedList* list);
#endif
