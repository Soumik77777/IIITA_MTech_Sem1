/*
Write a C program to separate an array into two arrays containing even and odd 
elements, respectively. 
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

    int a_even[n];
    int a_odd[n];
    int a_even_curr = 0;

    for (int i=0; i<n; i++) {
        if (a[i]%2 == 0) {
            a_even[a_even_curr] = a[i];
            a_even_curr ++;
        }
        else {
            a_odd[i - a_even_curr] = a[i];
        }
    }

    printf("The array containging even elements: ");
    for (int i=0; i<a_even_curr; i++) {
        printf("%d ", a_even[i]);
    }
    printf(" \n");

    printf("The array containging odd elements: ");
    for (int i=0; i<n-a_even_curr; i++) {
        printf("%d ", a_odd[i]);
    }
    printf(" \n");

}
