#include <iostream>
#ifdef PY36
	#include <python3.6m/Python.h>
#else
	#include <python3.5m/Python.h>
#endif
using namespace std;
/*
void transread(const char *host,const char *filepath,const char *targetdir,const char *uid,const char *gid,int position,int size);
void transupload(const char *host,const char *filepath,const char *targetdir);
*/
extern PyThreadState * mainThreadState;
