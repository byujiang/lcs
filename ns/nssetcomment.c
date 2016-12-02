/*
 * Copyright (C) 2000 by CERN/IT/PDP/DM
 * All rights reserved
 */

#ifndef lint
static char sccsid[] = "@(#)nssetcomment.c,v 1.1 2001/01/08 15:21:05 CERN IT-PDP/DM Jean-Philippe Baud";
#endif /* not lint */

/*	nssetcomment - add/replace a comment associated with a file/directory */
#include <errno.h>
#include <grp.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#if defined(_WIN32)
#include <winsock2.h>
#endif
#include "Cns.h"
#include "Cns_api.h"
#include "serrno.h"
extern	char	*getenv();
main(argc, argv)
int argc;
char **argv;
{
	int c;
	int errflg = 0;
	char fullpath[CA_MAXPATHLEN+1];
	char *p;
	char *path;
#if defined(_WIN32)
	WSADATA wsadata;
#endif

	if (argc < 3) {
		fprintf (stderr,
		    "usage: %s file comment\n", argv[0]);
		exit (USERR);
	}
#if defined(_WIN32)
	if (WSAStartup (MAKEWORD (2, 0), &wsadata)) {
		fprintf (stderr, NS052);
		exit (SYERR);
	}
#endif
	path = argv[1];
	if (*path != '/' && strstr (path, ":/") == NULL) {
		if ((p = getenv ("CASTOR_HOME")) == NULL ||
		    strlen (p) + strlen (path) + 1 > CA_MAXPATHLEN) {
			fprintf (stderr, "%s: invalid path\n", path);
			errflg++;
		} else
			sprintf (fullpath, "%s/%s", p, path);
	} else {
		if (strlen (path) > CA_MAXPATHLEN) {
			fprintf (stderr, "%s: %s\n", path,
			    sstrerror(SENAMETOOLONG));
			errflg++;
		} else
			strcpy (fullpath, path);
	}
	if (errflg == 0 && Cns_setcomment (fullpath, argv[2])) {
		fprintf (stderr, "%s: %s\n", path, sstrerror(serrno));
		errflg++;
	}
#if defined(_WIN32)
	WSACleanup();
#endif
	if (errflg)
		exit (USERR);
	exit (0);
}
