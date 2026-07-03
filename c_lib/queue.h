#ifndef QUEUE_H
#define QUEUE_H
typedef struct Queue { void** items; int front; int rear; int capacity; int size; } Queue;
Queue* queue_create(int capacity);
void enqueue(Queue* q, void* item);
void* dequeue(Queue* q);
int queue_is_empty(Queue* q);
void queue_free(Queue* q);
#endif
