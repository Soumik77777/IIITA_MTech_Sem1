/*
Write a program to create an array with n elements. For the user-given input, x, rotate
the array elements to the left with x positions.
For example, array a[ ] = {1, 2, 3, 4} and x = 2, then output should be a[ ] = {3, 4, 1, 2}
and for x = 5, output should be a[ ] = {2, 3, 4, 1}.
*/

#include <stdio.h>

int main () {
    int n;
    printf("Insert size of array:");
    scanf("%d", &n);

    int array[n];
    printf("Enter the integer elements of the array:\n");
    for (int i = 0; i < n; i++) {
        scanf("%d", &array[i]);
    }

    int x;
    printf("Please specify pivot index:");
    scanf("%d", &x);

    x = x % n;  // to handle if x>n

    int temp[n];
    for (int i = 0; i < n; i++) {
        temp[i] = array[(i + x) % n];
    }
    for (int i = 0; i < n; i++) {
        array[i] = temp[i];
    }

    printf("\nEditted array:\n");
    for (int i = 0; i < n; i++) {
        printf("%d ", array[i]);
    }

    return 0;
}