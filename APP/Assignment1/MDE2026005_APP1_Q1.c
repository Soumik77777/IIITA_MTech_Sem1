/*
Write a program to scan an integer array once and returns both the second-largest and
second-smallest distinct values via pointer, handling arrays that are too small or contain
duplicates only.
*/

#include <stdio.h>
#include <limits.h>

int find_second_largest_smallest(int n, int arr[n], int *second_largest, int *second_smallest) {
    if (n<2) {
        return 0; // array not large enough to have second largest
    }
    int largest = INT_MIN, sec_largest = INT_MIN;
    int smallest = INT_MAX, sec_smallest = INT_MAX;

    for (int i = 0; i<n; i++) {
        int x = arr[i];

        if (x > largest) {
            sec_largest = largest;
            largest = x;
        } else if (x < largest && x > sec_largest) {
            sec_largest = x;
        }

        if (x < smallest) {
            sec_smallest = smallest;
            smallest = x;
        } else if (x > smallest && x < sec_smallest) {
            sec_smallest = x;
        }
    }

    // for the case of less than 2 distinct values
    if (sec_largest == INT_MIN || sec_smallest == INT_MAX) {
        return 0;
    }

    *second_largest = sec_largest;
    *second_smallest = sec_smallest;
    return 1;

}


int main() {
    int size;
    printf("Insert size of array: ");
    scanf("%d", &size);

    int array[size];
    printf("Enter the integer elements of the array: ");
    for (int i = 0; i < size; i++) {
        scanf("%d", &array[i]);
    }

    int second_largest, second_smallest;
    int ok = find_second_largest_smallest(size, array, &second_largest, &second_smallest);

    if (ok) {
        printf("Second largest: %d\n", second_largest);
        printf("Second smallest: %d\n", second_smallest);
    } else {
        printf("Array too small or does not have enough distinct values.\n");
    }

    return 0;
}


