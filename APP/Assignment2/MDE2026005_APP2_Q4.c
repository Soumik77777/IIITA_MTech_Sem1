/*
Given an array of n integers, that may contain repeating elements. Write a C program to
print the unique elements along with the frequency of that element in the input array.
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

    int visited[n];
    for (int i =0; i < n; i++) {
        visited[i] = 0; // not visited
    }
    
    for (int i=0; i<n; i++) {
        if (visited[i] == 1) {
            continue;
        }
        int count = 1;
        for (int j = i+1; j<n; j++) {
            if (array[j] == array[i]) {
                count++;
                visited[j] = 1;
            }
        }
        printf("Element: %d; Frequency: %d.\n", array[i], count);
        visited[i] = 1;
    }

    return 0;
}