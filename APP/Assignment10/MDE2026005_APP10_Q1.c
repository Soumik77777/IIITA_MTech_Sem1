/*
Write a C program to sort an array containing both positive and negative integers such
that negative numbers appear first, followed by positive numbers. Maintain ascending
order within each group.
*/

#include<stdio.h>

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
  
  printf("Sorted array: \n");
  for (int i=0; i<n; i++) {
    printf("%d\n", a[i]);
  }
}
