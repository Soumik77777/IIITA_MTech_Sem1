/*
Write a C program that takes a string as input and compress the consecutive characters 
in the input string.
Example: input: aaabbcddddda output: a3b2c1d5a1.
*/

#include <stdio.h>

int main() {
    char str[100];
    printf("Enter a string: ");
    scanf("%s", str);

    int i = 0;
    printf("Compressed string: ");
    while (str[i] != '\0') {
        char current = str[i];
        int count = 0;

        while (str[i] == current) {
            count++;
            i++;
        }

        printf("%c%d", current, count);
    }
    printf("\n");

    return 0;
}