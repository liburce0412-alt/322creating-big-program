#include " binary_search.h\
int binary_search(int* a, int l, int r, int t) { while(l<=r){int m=l+(r-l)/2; if(a[m]==t)return m; if(a[m]<t)l=m+1; else r=m-1;} return -1; }
