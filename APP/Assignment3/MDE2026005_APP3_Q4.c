/*
Write a C program to calculate the length of the input string using recursion.
*/

#include <stdio.h>

int string_length(char *str) {
    if (*str == '\0') {
        return 0;
    }
    return 1 + string_length(str + 1);
}

int main() {
    char str[100];
    printf("Enter a string: ");
    scanf("%s", str);

    int len = string_length(str);
    printf("Length of string = %d\n", len);

    return 0;
}