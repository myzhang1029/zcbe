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
#include <slib/fileopt.h>
#include "builder.h"
#include "toml.h"

static int goodstrcmp(const char *line, const char *name)
{
    int n;
    while ((n = (*line++) - (*name++)) == 0)
        if (*line == 0 || *name == 0)
            return 0;
    return n;
}

static int finsert(FILE *file, const char *buffer)
{

    long insert_pos = ftell(file);
    char move_buffer[1024];
    if (insert_pos < 0)
        return insert_pos;

    int seek_ret = fseek(file, 0, SEEK_END);
    if (seek_ret)
        return seek_ret;
    long total_left_to_move = ftell(file);
    if (total_left_to_move < 0)
        return total_left_to_move;

    unsigned long ammount_to_grow = strlen(buffer);
    if (ammount_to_grow >= sizeof(move_buffer))
        return -1;

    total_left_to_move -= insert_pos;

    for (;;)
    {
        int ammount_to_move = sizeof(move_buffer);
        if (total_left_to_move < ammount_to_move)
            ammount_to_move = total_left_to_move;

        long read_pos = insert_pos + total_left_to_move - ammount_to_move;

        seek_ret = fseek(file, read_pos, SEEK_SET);
        if (seek_ret)
            return seek_ret;
        fread(move_buffer, ammount_to_move, 1, file);
        if (ferror(file))
            return ferror(file);

        seek_ret = fseek(file, read_pos + ammount_to_grow, SEEK_SET);
        if (seek_ret)
            return seek_ret;
        fwrite(move_buffer, ammount_to_move, 1, file);
        if (ferror(file))
            return ferror(file);

        total_left_to_move -= ammount_to_move;

        if (!total_left_to_move)
            break;
    }
    seek_ret = fseek(file, insert_pos, SEEK_SET);
    if (seek_ret)
        return seek_ret;
    fwrite(buffer, ammount_to_grow, 1, file);
    if (ferror(file))
        return ferror(file);

    return 0;
}

int is_dep_met(const char *name, int type)
{
    FILE *fp;
    char *pathname;
    char *env;
    if (type == 0) /* build */
        env = getenv("ZCTOP");
    else /* type == 1 -- host */
        env = getenv("ZCPREF");
    pathname = malloc(sizeof(char) * (strlen(env) + 10));
    if (pathname == NULL)
    {
        perror("is_dep_met: malloc");
        return -1;
    }
    strcpy(pathname, env);
    strcat(pathname, "/.metdeps");
    /* Using mode a in case the file does not exist */
    fp = fopen(pathname, "ab+");
    free(pathname);
    if (fp == NULL)
    {
        perror("is_dep_met: fopen");
        return -1;
    }
    if (slib_fbsearch(name, fp, goodstrcmp) != -1)
        return 1;
    else
        return 0;
}

int dep_is_met(const char *name, int type)
{
    FILE *fp;
    char *pathname;
    char *env;
    long *lines, lc, count;
    size_t szn = strlen(name);
    char *line = malloc(szn + 1);
    if (type == 0) /* build */
        env = getenv("ZCTOP");
    else /* type == 1 -- host */
        env = getenv("ZCPREF");
    pathname = malloc(sizeof(char) * (strlen(env) + 10));
    if (pathname == NULL)
    {
        perror("dep_is_met: malloc");
        return -1;
    }
    strcpy(pathname, env);
    strcat(pathname, "/.metdeps");
    fp = fopen(pathname, "ab+");
    free(pathname);
    if (fp == NULL)
    {
        perror("is_dep_met: fopen");
        return -1;
    }
    lines = slib_count_fl(fp, &lc);
    for (count = 0; count < lc; ++count)
    {
        int cmp;
        fseek(fp, lines[count], SEEK_SET);
        fgets(line, szn, fp);
        cmp = goodstrcmp(line, name);
        if (cmp > 0)
        {
            finsert(fp, name);
        }
        else if (cmp == 0)
        {
            /* Already there */
            return 0;
        }
        /* else continue; */
    }
    return 0;
}
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
                fprintf(stderr, "solve_dependencies_now: stopping due to unmet "
                                "build tool\n");
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
                fprintf(stderr,
                        "solve_dependencies_now: stopping due to unmet "
                        "dependency %s",
                        cur_dep_name);
                return 4;
            }
        }
    }
    return 0;
}
