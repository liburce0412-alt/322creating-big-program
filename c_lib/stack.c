#include <stdlib.h>
#include stack.h
Stack* stack_create(int cap) { Stack* s = malloc(sizeof(Stack)); s->items = malloc(sizeof(void*)*cap); s->top = -1; s->capacity = cap; return s; }
void stack_push(Stack* s, void* item) { if(s->top < s->capacity-1) s->items[++s->top] = item; }
void* stack_pop(Stack* s) { return s->top >= 0 ? s->items[s->top--] : NULL; }
void* stack_peek(Stack* s) { return s->top >= 0 ? s->items[s->top] : NULL; }
void stack_free(Stack* s) { free(s->items); free(s); }
