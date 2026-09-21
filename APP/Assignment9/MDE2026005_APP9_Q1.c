/*
Write a menu driven program for performing stack operations
such as PUSH, POP, finding top of the stack.
*/

#include <stdio.h>

#define MAX 100

int stack[MAX];
int top = -1;

void push(int data) {
    if (top == MAX - 1) {
        printf("Stack is full.\n");
        return;
    }

    top++;
    stack[top] = data;
    printf("Element pushed successfully.\n");
}

void pop() {
    if (top == -1) {
        printf("Stack is empty.\n");
        return;
    }

    printf("Deleted element: %d\n", stack[top]);
    top--;
}

void displayTop() {
    if (top == -1) {
        printf("Stack is empty.\n");
        return;
    }

    printf("Top element: %d\n", stack[top]);
}

void display() {
    if (top == -1) {
        printf("Stack is empty.\n");
        return;
    }

    printf("Stack: ");

    for (int i = top; i >= 0; i--)
        printf("%d ", stack[i]);

    printf("\n");
}

int main() {
    int choice, data;

    while (1) {
        printf("\n1. Push\n");
        printf("2. Pop\n");
        printf("3. Top\n");
        printf("4. Traverse\n");
        printf("5. Exit\n");

        printf("Enter choice: ");
        scanf("%d", &choice);

        if (choice == 5)
            break;

        if (choice == 1) {
            printf("Enter element: ");
            scanf("%d", &data);

            push(data);
        }
        else if (choice == 2) {
            pop();
        }
        else if (choice == 3) {
            displayTop();
        }
        else if (choice == 4) {
            display();
        }
        else {
            printf("Invalid choice.\n");
        }
    }

    return 0;
}
