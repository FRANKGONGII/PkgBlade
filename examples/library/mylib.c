#include <stdio.h>
// gcc -shared -fPIC -o libmylib.so mylib.c
void my_custom_function() {
    printf("Hello from mylib!\n");
}
