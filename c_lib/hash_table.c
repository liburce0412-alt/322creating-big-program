#include <stdlib.h>
#include <string.h>
#include " hash_table.h\
HashTable* ht_create(int s) { HashTable* h=malloc(sizeof(HashTable)); h->buckets=calloc(s,sizeof(HashEntry*)); h->size=s; return h; }
int hh(HashTable* h, const char* k) { unsigned long v=0; while(*k) v=v*31+(*k++); return v%h->size; }
void hp(HashTable* h, const char* k, void* v) { int i=hh(h,k); HashEntry* e=malloc(sizeof(HashEntry)); e->key=strdup(k); e->value=v; e->next=h->buckets[i]; h->buckets[i]=e; }
void* hg(HashTable* h, const char* k) { int i=hh(h,k); HashEntry* e=h->buckets[i]; while(e){if(strcmp(e->key,k)==0)return e->value;e=e->next;} return NULL; }
void hf(HashTable* h) { for(int i=0;i<h->size;i++){HashEntry* e=h->buckets[i]; while(e){HashEntry* n=e->next;free(e->key);free(e);e=n;}} free(h->buckets);free(h); }
