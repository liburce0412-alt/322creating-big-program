#ifndef HASH_TABLE_H
#define HASH_TABLE_H
typedef struct HashEntry { char* key; void* value; struct HashEntry* next; } HashEntry;
typedef struct { HashEntry** buckets; int size; } HashTable;
HashTable* ht_create(int size);
void ht_put(HashTable* ht, const char* key, void* value);
void* ht_get(HashTable* ht, const char* key);
void ht_free(HashTable* ht);
#endif
