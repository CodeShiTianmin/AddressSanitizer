/* LD_PRELOAD helper used once on the uninstrumented (base) binaries to
 * characterise allocation behaviour: number of heap allocations and their
 * size distribution. Written to $MALLOCCOUNT_DIR/<pid> at exit. */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

extern void *__libc_malloc(size_t);
extern void *__libc_calloc(size_t, size_t);
extern void *__libc_realloc(void *, size_t);
extern void *__libc_memalign(size_t, size_t);

static unsigned long long n_alloc, bytes, n_le16, n_le64, n_le256, n_big;

static inline void account(size_t sz) {
  n_alloc++; bytes += sz;
  if (sz <= 16) n_le16++; else if (sz <= 64) n_le64++; else if (sz <= 256) n_le256++; else n_big++;
}
void *malloc(size_t sz) { account(sz); return __libc_malloc(sz); }
void *calloc(size_t a, size_t b) { account(a * b); return __libc_calloc(a, b); }
void *realloc(void *p, size_t sz) { account(sz); return __libc_realloc(p, sz); }
int posix_memalign(void **r, size_t al, size_t sz) { account(sz); *r = __libc_memalign(al, sz); return *r ? 0 : 12; }
void *aligned_alloc(size_t al, size_t sz) { account(sz); return __libc_memalign(al, sz); }
void *memalign(size_t al, size_t sz) { account(sz); return __libc_memalign(al, sz); }

__attribute__((destructor)) static void malloccount_dump(void) {
  const char *dir = getenv("MALLOCCOUNT_DIR");
  if (!dir) return;
  char path[4096], exe[4096];
  ssize_t n = readlink("/proc/self/exe", exe, sizeof exe - 1);
  exe[n > 0 ? n : 0] = '\0';
  snprintf(path, sizeof path, "%s/%d", dir, (int)getpid());
  FILE *out = fopen(path, "w");
  if (!out) return;
  fprintf(out, "exe %s\nallocs %llu\nbytes %llu\nle16 %llu\nle64 %llu\nle256 %llu\ngt256 %llu\n",
          exe, n_alloc, bytes, n_le16, n_le64, n_le256, n_big);
  fclose(out);
}
