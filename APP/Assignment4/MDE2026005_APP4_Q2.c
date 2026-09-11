/*
Write a C program to create an array having 10 elements and initialize it with numbers 1 
to 10. Print the array. Take a pointer, say p,  point to the base address, and loop through 
the addresses to access each element address and increase the value at the address of 
each element by 2. Again, print the elements of the array.
*/

#include <stdio.h>

int main(void) {
    int arr[10];
    int *p;

    for (int i = 0; i < 10; i++) {
        arr[i] = i + 1;
    }

    printf("Original array: ");
    for (int i = 0; i < 10; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");

    p = arr;

    for (int i = 0; i < 10; i++) {
        *(p + i) += 2;
    }

    printf("Updated array: ");
    for (int i = 0; i < 10; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");

    return 0;
}