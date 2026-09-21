/*
Implement stack operations as in program 1 using
singly linked list instead of array.
program 1: Write a menu driven program for performing stack operations
such as PUSH, POP, finding top of the stack.
*/

#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *next;
};

struct Node* push(struct Node *top, int data) {
    struct Node *newNode = (struct Node*)malloc(sizeof(struct Node));

    newNode->data = data;
    newNode->next = top;

    return newNode;
}

struct Node* pop(struct Node *top) {
    if (top == NULL) {
        printf("Stack is empty.\n");
        return NULL;
    }

    struct Node *temp = top;

    printf("Deleted element: %d\n", top->data);

    top = top->next;
    free(temp);

    return top;
}

void displayTop(struct Node *top) {
    if (top == NULL) {
        printf("Stack is empty.\n");
        return;
    }

    printf("Top element: %d\n", top->data);
}

void display(struct Node *top) {
    if (top == NULL) {
        printf("Stack is empty.\n");
        return;
    }

    printf("Stack: ");

    while (top != NULL) {
        printf("%d ", top->data);
        top = top->next;
    }

    printf("\n");
}

void freeList(struct Node *top) {
    struct Node *temp;

    while (top != NULL) {
        temp = top;
        top = top->next;
        free(temp);
    }
}

int main() {
    int choice, data;
    struct Node *top = NULL;

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

            top = push(top, data);
        }
        else if (choice == 2) {
            top = pop(top);
        }
        else if (choice == 3) {
            displayTop(top);
        }
        else if (choice == 4) {
            display(top);
        }
        else {
            printf("Invalid choice.\n");
        }
    }

    freeList(top);

    return 0;
}