/*
Given an array of 0s, 1s, and 2s, rearrange it in a single pass so all 0s come first, then
all 1s, then all 2s, without using a counting/sorting library call. Time complexity should be
O(n) and space complexity should be O(1).
*/

#include <stdio.h>

void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

void sort_012(int n, int arr[]) {
    int low = 0, mid = 0, high = n - 1;

    while (mid <= high) {
        if (arr[mid] == 0) {
            swap(&arr[low], &arr[mid]);
            low++;
            mid++;
        } else if (arr[mid] == 1) {
            mid++;
        } else { // arr[mid] == 2
            swap(&arr[mid], &arr[high]);
            high--;
        }
    }
}

int main() {
    int n;
    printf("Enter number of elements: ");
    scanf("%d", &n);

    int arr[n];
    printf("Enter %d elements (only 0s, 1s, 2s): ", n);
    for (int i = 0; i < n; i++) {
        scanf("%d", &arr[i]);
    }

    sort_012(arr, n);

    printf("Rearranged array: ");
    for (int i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");

    return 0;
}



