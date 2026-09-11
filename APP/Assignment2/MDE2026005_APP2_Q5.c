/*
Given an array of integers, write a C program to find the index where the sum of
elements at the left-hand side of it is the same as the sum of elements at the right-hand
side of it.
For example: input array : -7 1 5 2 -4 3 0 , output: index = 3
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

    int total = 0;
    for (int i =0; i<n; i++) {
        total += array[i];
    }

    int left_sum = 0;
    int idx_found = 0; // purpose: boolean

    for (int i =0; i<n; i++) {
        int right_sum = total - left_sum - array[i];
        if (left_sum == right_sum) {
            printf("Desired index= %d", i);
            idx_found = 1;
            break;
        }
        left_sum += array[i];
    }

    if (!idx_found) {
        printf("No such index was found.");
    }

    return 0;
}