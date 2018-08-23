#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <errno.h>
#include <sys/time.h>
#include <pthread.h>
#include <math.h>
#include <queue>
#include "Cgetopt.h"
#include "Cns_api.h"
#include "serrno.h"
#include "u64subr.h"

#define VERSION 0.10
#define CACHEFILE "/dev/shm/data.json"
#define MAXURLLEN 256

int Vflag=0;

int helpflg=0;

static char conf_file[]="/etc/cdfs/cdfs.conf";

int proc(void){
        int res;
        char *ip=(char *)malloc(16);
        char *consol=(char *)malloc(8);
        char *tag=(char *)malloc(8);
        char *mdir=(char *)malloc(CA_MAXPATHLEN+1);
	char *ddir=(char *)malloc(128);
	char *basename=(char *)malloc(CA_MAXPATHLEN+1);
	char *url_path=(char *)malloc(MAXURLLEN+1);
	int filenum;
        int mtag;
        vector <string> filename;
        vector <struct Cns_filestat> st;
	vector <string> dv;
        string str_tmp;
	queue <string> dir;
	char path_tmp[CA_MAXPATHLEN+1];
	int mountdirnum=0;

        if(get_conf_value(conf_file, "DATA_SERVER_IP", ip)){
                fprintf(stderr, "Configyre file has no server IP\n");
                return -1;
        }
        if(get_conf_value(conf_file, "DATA_SERVER_CONSOL", consol)){
                fprintf(stderr, "Configure file has no server consol\n");
                return -1;
        }
        if(get_conf_value(conf_file, "MOUNT_TAG", tag)){
                fprintf(stderr,"Configure file has no mounttag\n");
                return -1;
        }else{
                mtag=atoi(tag);
        }
        if((res=get_conf_value(conf_file, "MOUNT_DIR", mdir)) && mtag==1){
                fprintf(stderr, "Configure file has no mountdir when mounttag=1\n");
                return -1;
        }else if(mtag==1 && res==0) {
                if(mdir[strlen(mdir)-1]=='/')
                        mdir[strlen(mdir)-1]='\0';
        }
	if(get_conf_value(conf_file, "DATA_DIR", ddir)){
                printf("Configure wrong\n");
                return 1;
	}else{
		str_tmp=ddir;
        	SplitString(str_tmp, dv);
	}
	mountdirnum=dv.size();
	for(int i = 0; i < mountdirnum; i++){
		if(dv[i][dv[i].length()-1]=='/'){
			dv[i][dv[i].length()-1]='\0';
		}
		dir.push(dv[i]);
	}
        uid_t uid=getuid();
        gid_t gid=getgid();

	while(!dir.empty()){
		strcpy(path_tmp, dir.front().c_str());
		dir.pop();
		sprintf(url_path, "http://%s:%s/list?uid=%d&gid=%d&path=%s", ip, consol, uid, gid, path_tmp);
		res=get_jsonbycurl(url_path, CACHEFILE);
		if(res){
			fprintf(stderr, "get_jsonbycurl failed\n");
			return 1;
		}
		res=get_metadatabyjson(CACHEFILE, filename, st);
		if(res==1){
			fprintf(stderr, "file not exist or not the data directoty\n");
			return 1;
		}else if(res==2) {//chyd
			fprintf(stderr, "DIR:%s\n", path_tmp);
			continue;
		}
                char *pathsplit=(char *)malloc(strlen(path_tmp)+1);
                strcpy(pathsplit, path_tmp);
                splitname(pathsplit, basename);
                filename[0]=basename;
                strcpy(st[0].name,basename);
                free(pathsplit);
		filenum=filename.size();
		for(int i=0; i<filenum; i++){
			if(mtag==1){
                        	if(create_vpath(mdir, st[i].path, st[i].filemode))
                                	return 1;
                         }
                         if(res=Cns_setmetadata(filename[i].c_str(), st[i])){
                                 fprintf(stderr, "file metadata insert failed\n");
                                 return 1;
                         }
			 if(st[i].filemode &S_IFDIR && i>0){
				 str_tmp=st[i].path;
				 dir.push(str_tmp);
			 } 
		}
		filename.clear();
		st.clear();	
	}	
	
	free(ip);
	free(consol);
	free(tag);
	free(mdir);
	free(ddir);
	free(basename);
	free(url_path);
	return res;
}

int main(int argc, char **argv)
{
	int c;
	int errflg=0;
        static struct Coptions longopts[] = {
                {"help", NO_ARGUMENT, &helpflg, 1},
                {"version", NO_ARGUMENT, &Vflag, 1},
                {0, 0, 0, 0}
	};
        Copterr = 1;
        Coptind = 1;
        while ((c = Cgetopt_long (argc, argv, "hV", longopts, NULL)) != EOF) {
                switch (c) {
                case 'V':
                        Vflag++;
                        break;
                case 'h':
                        helpflg++;
                        break;
                case '?':
                        errflg++;
                        break;
                default:
                        break;
                }
        }

        if (Coptind != argc && ! errflg) {      /* no file specified */
                errflg++;
        }
        if (errflg) {
                fprintf(stderr, "usage: %s [-hV] [--help version] ...\ninfo: load metadata from the remote station\n", argv[0]);
                exit (USERR);
        }
        if(Vflag){
                fprintf(stdout, "Version: %.2f\n", VERSION);
                exit(0);
        }
	if(helpflg){
		fprintf(stderr, "usage: %s [-hV] [--help version] ...\ninfo: load from the remote station\n", argv[0]);
		exit(0);
	}
	if(proc()){
		fprintf(stderr, "load metadata failed\n");
		errflg++;
	}
	
	if(errflg)
		exit(USERR);
	exit(0);	

}
