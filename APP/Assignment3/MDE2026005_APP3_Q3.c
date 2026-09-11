/*
Write a C program to print a string in reverse order using recursion. You need not store 
the characters of the string in an array or any other data structure.
*/


#include <stdio.h>

void print_reverse(char *str) {
    if (*str == '\0') {
        return;
    }
    print_reverse(str + 1);
    printf("%c", *str);
}

int main() {
    char str[100];
    printf("Enter a string: ");
    scanf("%s", str);

    printf("Reversed string: ");
    print_reverse(str);
    printf("\n");

    return 0;
}