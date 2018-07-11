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

#include <sys/types.h>
#include <unistd.h>
int build_now(void)
{
	pid_t pid;
	int status = 0;
	pid = fork();
	if(pid == 0)
		execlp("sh", "sh", "-e", "./zcbe/build.sh");
	else if (pid > 0)
		waitpid(pid, &status, 0);
	else
	{
		fprintf(stderr, "fork failed\n");
		return 2;
	}
	if (status != 0)
	{
		fprintf(stderr, "child exited with %d, stopping\n", status);
		return 1;
	}
	return 0;
}
