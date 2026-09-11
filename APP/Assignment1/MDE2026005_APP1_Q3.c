/*
Given two sorted integer arrays A (size m, with m+n capacity) and B (size n), merge B
into A in-place so A ends up sorted, without using extra array space.
*/

#include <stdio.h>


void merge_AB(int arr_A[], int m, int arr_B[], int n) {
    // check and compare last element of A and B, place the bigger at last
    int i = m - 1;       // last valid index in A's real data
    int j = n - 1;       // last valid index in B
    int k = m + n - 1;   // last index of merged A

    while (i >= 0 && j >= 0) {
        if (arr_A[i] > arr_B[j]) {
            arr_A[k] = arr_A[i];
            i--;
        } else {
            arr_A[k] = arr_B[j];
            j--;
        }
        k--;
    }

    // leftover elements of B
    while (j >= 0) {
        arr_A[k] = arr_B[j];
        j--;
        k--;
    }
}


int main() {
    int m;
    printf("Enter number of elements in A: ");
    scanf("%d", &m);

    int n;
    printf("Enter number of elements in B: ");
    scanf("%d", &n);

    int arr_A[m + n];
    printf("Enter %d sorted elements of A: ", m);
    for (int i = 0; i < m; i++) {
        scanf("%d", &arr_A[i]);
    }

    int arr_B[n];
    printf("Enter %d sorted elements of B: ", n);
    for (int i = 0; i < n; i++) {
        scanf("%d", &arr_B[i]);
    }

    merge_AB(arr_A, m, arr_B, n);

    printf("Merged array: ");
    for (int i = 0; i < m + n; i++) {
        printf("%d ", arr_A[i]);
    }
    printf("\n");

    return 0;
}

