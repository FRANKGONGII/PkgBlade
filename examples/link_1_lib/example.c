#include <stdio.h>

// 声明动态库中的函数
void my_custom_function();

int main() {
    printf("Calling function from custom library:\n");
    my_custom_function();
    return 0;
}
