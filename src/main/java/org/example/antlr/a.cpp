#include "tool_setup.h"
#include "tool_bname.h"
#include "memdebug.h" /* keep this as LAST include */
#ifndef HAVE_BASENAME
            
            char *tool_basename(char *path)
            {
              char *s1;
              char *s2;
            
              s1 = strrchr(path, '/');
              s2 = strrchr(path, '\\');
            
              if(s1 && s2) {
                path = (s1 > s2) ? s1 + 1 : s2 + 1;
              }
              else if(s1)
                path = s1 + 1;
              else if(s2)
                path = s2 + 1;
            
              return path;
            }