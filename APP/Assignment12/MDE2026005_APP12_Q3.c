// Question 3: Write a C program to find the k-th largest element in an array using a heap.
// Assumptions:
// 1. The array contains n integers.
// 2. The value of k satisfies 1 <= k <= n.
// 3. Duplicate elements are allowed and are counted as separate positions in descending sorted order.

#include <stdio.h>

void heapify(int arr[], int n, int i)
{
    int largest = i;
    int left = 2 * i + 1;
    int right = 2 * i + 2;
    int temp;

    if (left < n && arr[left] > arr[largest])
        largest = left;

    if (right < n && arr[right] > arr[largest])
        largest = right;

    if (largest != i)
    {
        temp = arr[i];
        arr[i] = arr[largest];
        arr[largest] = temp;

        heapify(arr, n, largest);
    }
}

int main()
{
    int arr[100];
    int n, k, i, temp;

    printf("Enter number of elements: ");
    scanf("%d", &n);

    if (n <= 0 || n > 100)
    {
        printf("Invalid array size!\n");
        return 1;
    }

    for (i = 0; i < n; i++)
    {
        printf("Enter element: ");
        scanf("%d", &arr[i]);
    }

    printf("Enter k: ");
    scanf("%d", &k);

    if (k < 1 || k > n)
    {
        printf("Invalid value of k!\n");
        return 1;
    }

    for (i = n / 2 - 1; i >= 0; i--)
        heapify(arr, n, i);

    for (i = 1; i < k; i++)
    {
        temp = arr[0];
        arr[0] = arr[n - 1];
        arr[n - 1] = temp;

        n--;
        heapify(arr, n, 0);
    }

    printf("K-th largest element: %d\n", arr[0]);

    return 0;
}