#include <stdlib.h>
#include " queue.h\
Queue* queue_create(int cap) { Queue* q=malloc(sizeof(Queue)); q->items=malloc(sizeof(void*)*cap); q->front=0; q->rear=-1; q->capacity=cap; q->size=0; return q; }
void enqueue(Queue* q, void* item) { if(q->size<q->capacity) { q->rear=(q->rear+1)%q->capacity; q->items[q->rear]=item; q->size++; } }
void* dequeue(Queue* q) { if(q->size==0) return NULL; void* item=q->items[q->front]; q->front=(q->front+1)%q->capacity; q->size--; return item; }
int queue_is_empty(Queue* q) { return q->size==0; }
void queue_free(Queue* q) { free(q->items); free(q); }
