/*
Write a C program to find the longest consecutive sequence in an array of integers
*/

#include<stdio.h>

int main () {
    int n;
    printf("Enter the size of the array: ");
    scanf("%d", &n);

    int a[n];
    printf("Enter the elements of the array:\n");
    for (int i = 0; i<n; i++) {
        scanf("%d", &a[i]);
    }

    int curr_loc = 0, curr_consecutive_length = 0;
    int longest_loc = 0, longest_consecutive_length = 0;

    for (int i = 0; i<n; i++) {
        if (a[i] == a[i-1]) {
            curr_consecutive_length ++;
        }

        else {
            curr_loc = i;
            curr_consecutive_length = 1;
        }

        if (curr_consecutive_length > longest_consecutive_length) {
            longest_consecutive_length = curr_consecutive_length;
            longest_loc = curr_loc;
        }
    }

    printf("The longest consecutive array:\n");
    for (int i = longest_loc; i<longest_loc+longest_consecutive_length; i++) {
        printf("%d ", a[i]);
    }
    printf("\nIt begins at location %d, with length %d.", longest_loc, longest_consecutive_length);

}
