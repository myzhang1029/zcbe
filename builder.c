/*
  builder.c - functions that actually do the build

   Copyright 2018 Zhang Maiyun.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include "toml.h"

int build_now(void)
{
	pid_t pid;
	int status = 0;
	pid = fork();
	if (pid == 0)
		execlp("sh", "sh", "-e", "./zcbe/build.sh");
	else if (pid > 0)
		waitpid(pid, &status, 0);
	else
	{
		perror("fork failed");
		return 2;
	}
	if (status != 0)
	{
		fprintf(stderr, "child exited with %d, stopping\n", status);
		return 1;
	}
	return 0;
}

int try_build_proj(char *proj_name)
{
	/* build.toml parsed before this */
	FILE *mapping_fp;
	toml_table_t *mapping;
	toml_table_t *cur_table;
	const char *raw;
	char *proj_dir;
	char errbuf[200];
	/* make sure we're at the top level */
	chdir(getenv("ZCTOP"));
	/* make sure we didn't encounter a circular dependency */
	if (check_for_circular(proj_name))
	{
		fprintf(stderr, "try_build_proj: circular dependency detected while processing %s\n", proj_name);
		return 1;
	}
	/* get project name to project dir mapping */
	if ((mapping_fp = fopen("mapping.toml", "r")) == NULL)
	{
		perror("fopen: mapping.toml");
		return 2;
	}
	mapping = toml_parse_file(mapping_fp, errbuf, sizeof(errbuf));
	fclose(mapping_fp);
	if (mapping == NULL)
	{
		fprintf(stderr, "toml_parse_file: mapping.toml: %s\n", errbuf);
		return 3;
	}
	/* get the [mapping] table */
	if ((cur_table = toml_table_in(mapping, "mapping")) == NULL)
	{
		fprintf(stderr, "try_build_proj: invalid mapping.toml found\n");
		toml_free(mapping);
		return 4;
	}
	if ((raw = toml_raw_in(cur_table, proj_name)) == NULL)
	{
		fprintf(stderr, "try_build_proj: project \"%s\" not found in mapping.toml\n", proj_name);
		toml_free(mapping);
		return 4;
	}
	if (toml_rtos(raw, &proj_dir))
	{
		fprintf(stderr, "toml_rtos: failed to extract proj_dir\n");
		toml_free(mapping);
		return 5;
	}
	toml_free(mapping);
	chdir(proj_dir);
	check_for_dependencies_now();
	if (build_now() != 0)
	{
		fprintf(stderr, "build_now returned with a non-zero value\n");
		return 6;
	}
	/* Successfully built proj */
	push_done_dep(proj_name);
	return 0;
}
