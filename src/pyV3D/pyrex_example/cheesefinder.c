/*
 *   An example of a C API that provides a callback mechanism.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "cheesefinder.h"

static char *cheeses[] = {
  "cheddar",
  "camembert",
  "that runny one",
  0
};

void find_cheeses(cheesefunc user_func, void *user_data) {
  char **p = cheeses;
  while (*p) {
    int status = user_func(*p, user_data);
    fprintf(stdout, "return = %d\n", status);
    ++p;
  }
}

