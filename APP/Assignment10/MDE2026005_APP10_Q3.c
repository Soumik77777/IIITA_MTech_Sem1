/*
Write a C program to sort the array of integers using quicksort or mergesort algorithm.
*/

#include <stdio.h>

void swap (int *x, int *y) {
  int temp = *x;
  *x = *y;
  *y = temp;
}

int partition (int a[], int low, int high) {
  int pivot = a[high];
  int i = low - 1;
  int j;
  
  for (j= low; j<high; j++) {
    if (a[j] <= pivot) {
      i++;
      swap(&a[i], &a[j]);
    }
  }
  
  swap(&a[i+1], &a[high]);
  
  return i+1;
}

void quicksort (int a[], int low, int high) {
  int p;
  
  if (low<high) {
    p = partition(a, low, high);
    
    quicksort(a, low, p-1);
    quicksort(a, p+1, high);
  }
}

void main () {
  int n;
  printf("Number of elements in the array: ");
  scanf("%d", &n);
  
  int a[n];
  printf("Enter array elements:\n");
  for (int i=0; i<n; i++) {
    scanf("%d", &a[i]);
  }
  
  quicksort(a, 0, n-1);
  
  printf("Sorted array: \n");
  for (int i=0; i<n; i++) {
    printf("%d\n", a[i]);
  }
}
