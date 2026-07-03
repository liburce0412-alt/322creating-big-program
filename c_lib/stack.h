#ifndef STACK_H
#define STACK_H
typedef struct Stack { void** items; int top; int capacity; } Stack;
Stack* stack_create(int capacity);
void stack_push(Stack* s, void* item);
void* stack_pop(Stack* s);
void* stack_peek(Stack* s);
void stack_free(Stack* s);
#endif
