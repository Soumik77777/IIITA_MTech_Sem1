/*
Write a program to count the number of nodes in a singly linked list.
*/

#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *next;
};

struct Node *createNode(int data)
{
    struct Node *newNode = malloc(sizeof(struct Node));

    if (newNode == NULL) {
        printf("Memory allocation failed.\n");
        return NULL;
    }

    newNode->data = data;
    newNode->next = NULL;

    return newNode;
}

void insert(struct Node **head, int data)
{
    struct Node *newNode;
    struct Node *current;

    newNode = createNode(data);

    if (newNode == NULL) {
        return;
    }

    if (*head == NULL) {
        *head = newNode;
        return;
    }

    current = *head;

    while (current->next != NULL) {
        current = current->next;
    }

    current->next = newNode;
}

int countNodes(struct Node *head)
{
    int count = 0;
    struct Node *current = head;

    while (current != NULL) {
        count++;
        current = current->next;
    }

    return count;
}

int returnValue(int n)
{
    return n;
}

void display(struct Node *head)
{
    struct Node *current = head;

    if (current == NULL) {
        printf("List is empty.\n");
        return;
    }

    while (current != NULL) {
        printf("%d", current->data);

        if (current->next != NULL) {
            printf(" -> ");
        }

        current = current->next;
    }

    printf("\n");
}

void freeList(struct Node *head)
{
    struct Node *temp;

    while (head != NULL) {
        temp = head;
        head = head->next;
        free(temp);
    }
}

int main(void)
{
    struct Node *head = NULL;
    int choice;
    int value;
    int n;

    do {
        printf("\n----- MENU -----\n");
        printf("1. Insert new element\n");
        printf("2. Count number of nodes\n");
        printf("3. Exit\n");
        printf("Enter your choice: ");

        if (scanf("%d", &choice) != 1) {
            printf("Invalid input.\n");
            freeList(head);
            return EXIT_FAILURE;
        }

        switch (choice) {
        case 1:
            printf("Enter element: ");

            if (scanf("%d", &value) != 1) {
                printf("Invalid input.\n");
                freeList(head);
                return EXIT_FAILURE;
            }

            insert(&head, value);

            printf("Element inserted.\n");
            printf("Linked list: ");
            display(head);
            break;

        case 2:
            printf("Number of nodes: %d\n", countNodes(head));
            break;

        case 3:
            printf("Exiting program.\n");
            break;

        default:
            printf("Enter an integer n: ");

            if (scanf("%d", &n) != 1) {
                printf("Invalid input.\n");
                freeList(head);
                return EXIT_FAILURE;
            }

            printf("Returned value: %d\n", returnValue(n));
            break;
        }

    } while (choice != 3);

    freeList(head);

    return EXIT_SUCCESS;
}