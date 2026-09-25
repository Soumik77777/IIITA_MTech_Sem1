/*
Write a C program to sort an array using Bubble Sort and then remove all duplicate
elements from the sorted array. Display the resulting array.
*/

#include <stdio.h>

void main () {
  int n;
  printf("Number of elements in the array: ");
  scanf("%d", &n);
  
  int a[n];
  printf("Enter array elements:\n");
  for (int i=0; i<n; i++) {
    scanf("%d", &a[i]);
  }
  
  int temp;
  for (int i=0; i<n-1; i++) {
    for (int j=0; j<n-i-1; j++) {
      if (a[j] > a[j+1]) {
        temp = a[j];
        a[j] = a[j+1];
        a[j+1] = temp;
      }
    }
  }
  printf("Sorted array (Bubble Sort): \n");
  for (int i=0; i<n; i++) {
    printf("%d\n", a[i]);
  }
  
  int k;
  for (int i=0; i<n; i++) {
    if (i==0 || a[i] != a[i - 1]) {
      a[k++] = a[i];
    }
  }
  printf("Removed duplicate array: \n");
  for (int i=0; i<k; i++) {
    printf("%d\n", a[i]);
  }
}
