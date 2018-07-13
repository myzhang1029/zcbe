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

#include <stdio.h>
#include "toml.h"

int solve_dependencies_now(void)
{
	FILE *conf_fp;
	int i, j;
	toml_table_t conf;
	toml_table_t *cur_table;
	toml_array_t *cur_array;
	const char *raw;
	char *cur_dep_name;
	char errbuf[200];
	char possible_types[][] = {
		"req",
		"rec",
		"opt"
	};
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
		while((raw = toml_raw_at(cur_array, i++)))
		{
			if(toml_rtos(raw, &cur_dep_name))
			{
				fprintf(stderr, "solve_dependencies_now: toml_rtos failed\n");
				toml_free(conf);
				return 3;
			}
			if(is_dep_met(cur_dep_name, 0))
			{
				free(cur_dep_name);
				continue;
			}
			printf("Is \"%s\" installed on your computer [y/n]?", cur_dep_name);
			if(getchar() != 'y')
			{
				printf("'No' selected\n");
				fprintf(stderr, "solve_dependencies_now: stopping due to unmet build tool\n");
				free(cur_dep_name);
				toml_free(conf);
				return 3;
			}
			else
				dep_is_met(cur_dep_name, 0);/* cache this */
		}
	}
	for (int i = 0; i < 3; ++i)
	{
		if ((cur_array = toml_array_in(cur_table, possible_types[i])) == NULL)
			continue;
		for (int j = 0;; ++j)
		{
			/* solve it */
		}
	}
