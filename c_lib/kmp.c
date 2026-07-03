#include <stdlib.h>
#include <string.h>
#include \kmp.h\
int* kmp_build_lps(const char* p) { int m=strlen(p); int* lps=malloc(sizeof(int)*m); int len=0; lps[0]=0; int i=1; while(i<m) { if(p[i]==p[len]) { len++; lps[i]=len; i++; } else { if(len) len=lps[len-1]; else { lps[i]=0; i++; } } } return lps; }
int kmp_search(const char* t, const char* p) { int n=strlen(t), m=strlen(p); int* lps=kmp_build_lps(p); int i=0, j=0; while(i<n) { if(t[i]==p[j]) { i++; j++; } if(j==m) { free(lps); return i-j; } else if(i<n&&t[i]!=p[j]) { if(j) j=lps[j-1]; else i++; } } free(lps); return -1; }
