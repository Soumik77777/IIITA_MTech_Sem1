/*
Write a C program to maintain three separate singly linked lists using three
head nodes. Provide options to insert elements into any selected list and
display all three lists.
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

void display(struct Node *head) {
    if (head == NULL) {
        printf("Empty");
        return;
    }

    while (head != NULL) {
        printf("%d ", head->data);
        head = head->next;
    }
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
    struct Node *head1 = NULL;
    struct Node *head2 = NULL;
    struct Node *head3 = NULL;

    int choice, data;

    while (1) {
        printf("\n1. Insert into List 1\n");
        printf("2. Insert into List 2\n");
        printf("3. Insert into List 3\n");
        printf("4. Display all lists\n");
        printf("5. Exit\n");

        printf("Enter choice: ");
        scanf("%d", &choice);

        if (choice == 5)
            break;

        if (choice >= 1 && choice <= 3) {
            printf("Enter element: ");
            scanf("%d", &data);

            if (choice == 1)
                head1 = insert(head1, data);
            else if (choice == 2)
                head2 = insert(head2, data);
            else
                head3 = insert(head3, data);
        }
        else if (choice == 4) {
            printf("\nList 1: ");
            display(head1);

            printf("\nList 2: ");
            display(head2);

            printf("\nList 3: ");
            display(head3);

            printf("\n");
        }
        else {
            printf("Invalid choice.\n");
        }
    }

    freeList(head1);
    freeList(head2);
    freeList(head3);

    return 0;
}