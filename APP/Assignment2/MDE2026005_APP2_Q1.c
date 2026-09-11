/*
Write a program to reverse an array of integers without using any additional array.
*/

#include <stdio.h>

int main() {
    int n;
    printf("Insert size of array: ");
    scanf("%d", &n);

    int array[n];
    printf("Enter the integer elements of the array: ");
    for (int i = 0; i < n; i++) {
        scanf("%d", &array[i]);
    }

    printf("Input array:");
    for (int i = 0; i < n; i++) {
        printf("%d ", array[i]);
    }

    int start = 0, end = n-1;
    while (start < end) {
        int temp = array[start];
        array[start] = array[end];
        array[end] = temp;
        start++;
        end--;
    }

    printf("\nReversed array:");
    for (int i = 0; i < n; i++) {
        printf("%d ", array[i]);
    }

    return 0;
}