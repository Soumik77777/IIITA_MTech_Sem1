/*
Write a C program to swap two numbers. Make two functions named as call_by_value 
and call_by_reference to pass the value/reference of two variables for swapping.
*/


#include <stdio.h>

void call_by_value(int a, int b) {
    int temp = a;
    a = b;
    b = temp;
    printf("Inside call_by_value: a = %d, b = %d\n", a, b);
}

void call_by_reference(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

int main() {
    int x, y;
    printf("Enter two numbers: ");
    scanf("%d %d", &x, &y);

    call_by_value(x, y);
    printf("After call_by_value, in main: x = %d, y = %d (unchanged)\n", x, y);

    call_by_reference(&x, &y);
    printf("After call_by_reference, in main: x = %d, y = %d (swapped)\n", x, y);

    return 0;
}
