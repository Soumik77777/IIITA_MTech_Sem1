/*
Write a C program to count the number of vowels and consonants using recursion. 
*/

#include <stdio.h>

void count(char str[], int i, int *vowels, int *consonants) {
    if (str[i] == '\0')
        return;

    if (str[i] == 'a' || str[i] == 'e' || str[i] == 'i' ||
        str[i] == 'o' || str[i] == 'u' ||
        str[i] == 'A' || str[i] == 'E' || str[i] == 'I' ||
        str[i] == 'O' || str[i] == 'U') {
        (*vowels)++;
    }
    else if ((str[i] >= 'a' && str[i] <= 'z') ||
             (str[i] >= 'A' && str[i] <= 'Z')) {
        (*consonants)++;
    }

    count(str, i + 1, vowels, consonants);
}

int main() {
    char str[100];
    int vowels = 0, consonants = 0;

    printf("Enter a string: ");
    fgets(str, sizeof(str), stdin);

    count(str, 0, &vowels, &consonants);

    printf("Number of vowels: %d\n", vowels);
    printf("Number of consonants: %d\n", consonants);

    return 0;
}

