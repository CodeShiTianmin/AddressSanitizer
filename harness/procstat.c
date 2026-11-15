/* LD_PRELOAD helper: at process exit, copy the Vm* lines of /proc/self/status
 * into $PROCSTAT_DIR/<pid>. The paper measured memory the same way
 * (VmPeak / VmStk read from /proc/self/status at termination). */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

__attribute__((destructor)) static void procstat_dump(void) {
  const char *dir = getenv("PROCSTAT_DIR");
  if (!dir) return;
  char path[4096], exe[4096], line[512];
  ssize_t n = readlink("/proc/self/exe", exe, sizeof exe - 1);
  exe[n > 0 ? n : 0] = '\0';
  snprintf(path, sizeof path, "%s/%d", dir, (int)getpid());
  FILE *in = fopen("/proc/self/status", "r"), *out = fopen(path, "w");
  if (in && out) {
    fprintf(out, "Exe:\t%s\n", exe);
    while (fgets(line, sizeof line, in))
      if (strncmp(line, "Vm", 2) == 0) fputs(line, out);
  }
  if (in) fclose(in);
  if (out) fclose(out);
}
