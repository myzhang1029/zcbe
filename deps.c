/*
  deps.c - functions that solve dependencies

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

#include "deps.h"
#include <stdint.h>/* toml needs this */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "builder.h"
#include "toml.h"

int goodstrcmp(char *line, char *name)
{
	int n;
	while ((n = (*line++) - (*name++)) == 0)
		if (*line == 0 || *name == 0)
			return 0;
	return n;
}
int is_dep_met(char *name, int type)
{
	FILE *fp;
	char *pathname;
	char *env;
	char line[36];
	long filesize, oldfs, base = 0;
	int cmpdiff;
	if (type == 0) /* build */
		env = getenv("ZCTOP");
	else /* type == 1 -- host */
		env = getenv("ZCPREF");
	pathname = malloc(sizeof(char) * (strlen(env) + 10));
	if (pathname == NULL)
	{
		perror("is_dep_met: malloc");
		return 0;
	}
	strcpy(pathname, env);
	strcat(pathname, "/.metdeps");
	fp = fopen(pathname, "a+");
	if (fp == NULL)
	{
		perror("is_dep_met: fopen");
		free(pathname);
		return 0;
	}
	/* size of the file */
	fseek(fp, 0, SEEK_END);
	filesize = ftell(fp);
	while (1) /* bsearch the depname */
	{
		oldfs = filesize;
		filesize /= 2;
		if (oldfs == filesize)
		{
			/* cannot move anymore */
			fclose(fp);
			free(pathname);
			return 0;
		}
		fseek(fp, base + filesize, SEEK_SET);
		if (fgets(line, 36, fp) == NULL)
		{
			if (ferror(fp))
				perror("is_dep_met: fgets");
			fclose(fp);
			free(pathname);
			return 0;
		}
		/* good, we found it */
		if ((cmpdiff = goodstrcmp(line, name)) == 0)
		{
			fclose(fp);
			free(pathname);
			return 1;
		}
		else if (cmpdiff < 0)
			continue;
		else /* cmpdiff > 0 */
			base = filesize;
	}
}

int dep_is_met(char *name, int type) { return 0; }
int check_for_circular(char *cur_proj_name) { return 0; }
int solve_dependencies_now(void)
{
	FILE *conf_fp;
	int i, j;
	toml_table_t *conf;
	toml_table_t *cur_table;
	toml_array_t *cur_array;
	const char *raw;
	char *cur_dep_name;
	char errbuf[200];
	char *possible_types[] = {"req", "rec", "opt"};
	if ((conf_fp = fopen("zcbe/conf.toml", "r")) == NULL)
	{
		perror("fopen: conf.toml");
		return 1;
	}
	conf = toml_parse_file(conf_fp, errbuf, sizeof(errbuf));
	fclose(conf_fp);
	if (conf == NULL)
	{
		fprintf(stderr, "toml_parse_file: conf.toml: %s\n", errbuf);
		return 2;
	}
	if ((cur_table = toml_table_in(conf, "deps")) == NULL)
	{
		/* no dependencies */
		toml_free(conf);
		return 0;
	}
	if ((cur_array = toml_array_in(cur_table, "build")))
	{
		i = 0;
		while ((raw = toml_raw_at(cur_array, i++)))
		{
			if (toml_rtos(raw, &cur_dep_name))
			{
				fprintf(stderr, "solve_dependencies_now: toml_rtos failed\n");
				toml_free(conf);
				return 3;
			}
			if (is_dep_met(cur_dep_name, 0))
			{
				free(cur_dep_name);
				continue;
			}
			printf("Is \"%s\" installed on your computer [y/n]?", cur_dep_name);
			if (getchar() != 'y')
			{
				printf("'No' selected\n");
				fprintf(stderr, "solve_dependencies_now: stopping due to unmet build tool\n");
				free(cur_dep_name);
				toml_free(conf);
				return 3;
			}
			else
				dep_is_met(cur_dep_name, 0); /* cache this */
		}
	}
	for (int i = 0; i < 3; ++i)
	{
		if ((cur_array = toml_array_in(cur_table, possible_types[i])) == NULL)
			continue;
		j = 0;
		while ((raw = toml_raw_at(cur_array, j++)))
		{
			/* solve them with try_build_proj */
			if (toml_rtos(raw, &cur_dep_name))
			{
				fprintf(stderr, "solve_dependencies_now: toml_rtos failed\n");
				toml_free(conf);
				return 3;
			}
			if (is_dep_met(cur_dep_name, 1))
			{
				free(cur_dep_name);
				continue;
			}
			if (try_build_proj(cur_dep_name) != 0)
			{
				fprintf(stderr, "try_build_proj returned non-zero\n");
				fprintf(stderr, "solve_dependencies_now: stopping due to unmet dependency %s",
					cur_dep_name);
				return 4;
			}
		}
	}
	return 0;
}
