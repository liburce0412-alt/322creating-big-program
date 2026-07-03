#include <stdlib.h>
#include <string.h>
#include  linked_list.h
LinkedList* ll_create() { LinkedList* l = malloc(sizeof(LinkedList)); l->head = l->tail = NULL; l->size = 0; return l; }
void ll_append(LinkedList* list, void* data) { Node* n = malloc(sizeof(Node)); n->data = data; n->next = NULL; n->prev = list->tail; if(list->tail) list->tail->next = n; else list->head = n; list->tail = n; list->size++; }
void ll_free(LinkedList* list) { Node* cur = list->head; while(cur) { Node* next = cur->next; free(cur); cur = next; } free(list); }
