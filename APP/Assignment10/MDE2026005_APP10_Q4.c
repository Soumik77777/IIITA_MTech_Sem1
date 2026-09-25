/*
Write a C program to sort an array using Selection Sort and display the array after every
pass of the sorting process.
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
  
  for (int i=0; i<n; i++) {
    int min_idx = i;
    for (int j=i+1; j<n; j++) {
      if (a[j] < a[min_idx]) {
        min_idx = j;
      }
    }
    
    int temp = a[i];
    a[i] = a[min_idx];
    a[min_idx] = temp;
    
    printf("After loop %d: \n", i+1);
    for (int k=0; k<n; k++) {
      printf("%d ", a[k]);
    }
    printf("\n");
  }
}
