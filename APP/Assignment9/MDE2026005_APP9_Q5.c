/*
Implement Circular Queue and perform operations on it
using doubly circular linked list instead of array.
*/

#include <stdio.h>
#include <stdlib.h>

struct Node {
    int data;
    struct Node *next;
    struct Node *prev;
};

struct Node *front = NULL;
struct Node *rear = NULL;

void enqueue(int data) {
    struct Node *newNode = (struct Node*)malloc(sizeof(struct Node));

    newNode->data = data;

    if (front == NULL) {
        newNode->next = newNode;
        newNode->prev = newNode;

        front = newNode;
        rear = newNode;
    }
    else {
        newNode->next = front;
        newNode->prev = rear;

        rear->next = newNode;
        front->prev = newNode;

        rear = newNode;
    }

    printf("Element inserted successfully.\n");
}

void dequeue() {
    if (front == NULL) {
        printf("Queue is empty.\n");
        return;
    }

    struct Node *temp = front;

    printf("Deleted element: %d\n", front->data);

    if (front == rear) {
        front = NULL;
        rear = NULL;
    }
    else {
        front = front->next;

        front->prev = rear;
        rear->next = front;
    }

    free(temp);
}

void checkEmpty() {
    if (front == NULL)
        printf("Queue is empty.\n");
    else
        printf("Queue is not empty.\n");
}

void display() {
    if (front == NULL) {
        printf("Queue is empty.\n");
        return;
    }

    printf("Queue: ");

    struct Node *curr = front;

    do {
        printf("%d ", curr->data);
        curr = curr->next;
    } while (curr != front);

    printf("\n");
}

void freeQueue() {
    if (front == NULL)
        return;

    struct Node *curr = front->next;
    struct Node *temp;

    while (curr != front) {
        temp = curr;
        curr = curr->next;
        free(temp);
    }

    free(front);

    front = NULL;
    rear = NULL;
}

int main() {
    int choice, data;

    while (1) {
        printf("\n1. Enqueue\n");
        printf("2. Dequeue\n");
        printf("3. Check Empty\n");
        printf("4. Traverse\n");
        printf("5. Exit\n");

        printf("Enter choice: ");
        scanf("%d", &choice);

        if (choice == 5)
            break;

        if (choice == 1) {
            printf("Enter element: ");
            scanf("%d", &data);

            enqueue(data);
        }
        else if (choice == 2) {
            dequeue();
        }
        else if (choice == 3) {
            checkEmpty();
        }
        else if (choice == 4) {
            display();
        }
        else {
            printf("Invalid choice.\n");
        }
    }

    freeQueue();

    return 0;
}