/*
Write a C program to create multiple singly linked lists using multiple head
pointers. Allow the user to select a particular list and perform insertion,
deletion, and traversal on it.
*/

#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *next;
};

struct Node* insert(struct Node *head, int data) {
    struct Node *newNode = (struct Node*)malloc(sizeof(struct Node));

    newNode->data = data;
    newNode->next = NULL;

    if (head == NULL)
        return newNode;

    struct Node *curr = head;

    while (curr->next != NULL)
        curr = curr->next;

    curr->next = newNode;

    return head;
}

struct Node* delete(struct Node *head, int data) {
    if (head == NULL)
        return NULL;

    if (head->data == data) {
        struct Node *temp = head;
        head = head->next;
        free(temp);
        return head;
    }

    struct Node *curr = head;

    while (curr->next != NULL && curr->next->data != data)
        curr = curr->next;

    if (curr->next != NULL) {
        struct Node *temp = curr->next;
        curr->next = temp->next;
        free(temp);
    }

    return head;
}

void display(struct Node *head) {
    if (head == NULL) {
        printf("List is empty.\n");
        return;
    }

    while (head != NULL) {
        printf("%d ", head->data);
        head = head->next;
    }

    printf("\n");
}

void freeList(struct Node *head) {
    struct Node *temp;

    while (head != NULL) {
        temp = head;
        head = head->next;
        free(temp);
    }
}

int main() {
    int n, list, choice, data;
    struct Node **heads;

    printf("Enter number of lists: ");
    scanf("%d", &n);

    heads = (struct Node**)calloc(n, sizeof(struct Node*));

    while (1) {
        printf("\n1. Insert\n");
        printf("2. Delete\n");
        printf("3. Traverse\n");
        printf("4. Exit\n");

        printf("Enter choice: ");
        scanf("%d", &choice);

        if (choice == 4)
            break;

        printf("Select list (1-%d): ", n);
        scanf("%d", &list);

        if (list < 1 || list > n) {
            printf("Invalid list.\n");
            continue;
        }

        if (choice == 1) {
            printf("Enter element: ");
            scanf("%d", &data);

            heads[list - 1] = insert(heads[list - 1], data);
        }
        else if (choice == 2) {
            printf("Enter element to delete: ");
            scanf("%d", &data);

            heads[list - 1] = delete(heads[list - 1], data);
        }
        else if (choice == 3) {
            printf("List %d: ", list);
            display(heads[list - 1]);
        }
        else {
            printf("Invalid choice.\n");
        }
    }

    for (int i = 0; i < n; i++)
        freeList(heads[i]);

    free(heads);

    return 0;
}