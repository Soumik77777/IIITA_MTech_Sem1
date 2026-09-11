/*
Take a 3-dimensional array, say a[p][r][c], where p denotes planes, each with r rows and
c columns. Initialize the array with numbers sequentially from 1 to p*r*c, and take a
pointer, x, pointing to the base address of the array. Write a program to print the last
element of each plane accessed through the pointer.
*/

#include <stdio.h>

int main () {
    int p, r, c;
    printf("Insert size of array, in order- plane, row, column:\n");
    scanf("%d %d %d", &p, &r, &c);

    int a[p][r][c];

    int value = 1;
    for (int i = 0; i < p; i++) {
        for (int j = 0; j < r; j++) {
            for (int k = 0; k < c; k++) {
                a[i][j][k] = value;
                value++;
            }
        }
    }

    int *x = &a[0][0][0];
    for (int i = 0; i < p; i++) {
        int print_idx = (i + 1) * r * c - 1;
        printf("Last element of plane %d is %d.\n", i, *(x + print_idx));
    }

    return 0;
    
}