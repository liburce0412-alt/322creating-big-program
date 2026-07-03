#ifndef KMP_H
#define KMP_H
int* kmp_build_lps(const char* pattern);
int kmp_search(const char* text, const char* pattern);
#endif
