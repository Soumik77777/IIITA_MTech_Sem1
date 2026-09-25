/*
Write a C program to sort an array of integers according to their absolute values. For
example, -2, 1, -5, 3 should be arranged as 1, -2, 3, -5.
*/

#include <stdio.h>
#include <stdlib.h>

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
      if (abs(a[j]) < abs(a[min_idx])) {
        min_idx = j;
      }
    }
    
    int temp = a[i];
    a[i] = a[min_idx];
    a[min_idx] = temp;
    
  }
  printf("Final array: \n");
  for (int k=0; k<n; k++) {
    printf("%d ", a[k]);
  }
  printf("\n")
}
