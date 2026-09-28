/*
Write a program to search for a given value in a singly linked list.
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
        fprintf(stderr, "Memory allocation failed.\n");
        return NULL;
    }

    newNode->data = data;
    newNode->next = NULL;

    return newNode;
}

int search(struct Node *head, int value)
{
    struct Node *current = head;
    int position = 1;

    while (current != NULL) {
        if (current->data == value) {
            return position;
        }

        current = current->next;
        position++;
    }

    return -1;
}

void display(struct Node *head)
{
    struct Node *current = head;

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
    struct Node *newNode;
    struct Node *current;
    int n;
    int value;
    int searchValue;
    int position;

    printf("Enter number of nodes: ");
    if (scanf("%d", &n) != 1 || n < 0) {
        fprintf(stderr, "Invalid number of nodes.\n");
        return EXIT_FAILURE;
    }

    printf("Enter %d elements:\n", n);

    for (int i = 0; i < n; i++) {
        if (scanf("%d", &value) != 1) {
            fprintf(stderr, "Invalid input.\n");
            freeList(head);
            return EXIT_FAILURE;
        }

        newNode = createNode(value);
        if (newNode == NULL) {
            freeList(head);
            return EXIT_FAILURE;
        }

        if (head == NULL) {
            head = newNode;
        } else {
            current = head;

            while (current->next != NULL) {
                current = current->next;
            }

            current->next = newNode;
        }
    }

    printf("Linked list: ");
    display(head);

    printf("Enter value to search: ");
    if (scanf("%d", &searchValue) != 1) {
        fprintf(stderr, "Invalid input.\n");
        freeList(head);
        return EXIT_FAILURE;
    }

    position = search(head, searchValue);

    if (position != -1) {
        printf("Value %d found at position %d.\n",
               searchValue, position);
    } else {
        printf("Value %d not found in the linked list.\n",
               searchValue);
    }

    freeList(head);

    return EXIT_SUCCESS;
}