/*
Write a C Program to implement Queue using an array.
The program should be menu-driven, with the option to enqueue,
and dequeue, to check whether the queue is empty or full,
traverse, and exit based on the user's choice.
*/

#include <stdio.h>

#define MAX 100

int queue[MAX];
int front = -1;
int rear = -1;

void enqueue(int data) {
    if (rear == MAX - 1) {
        printf("Queue is full.\n");
        return;
    }

    if (front == -1)
        front = 0;

    rear++;
    queue[rear] = data;

    printf("Element inserted successfully.\n");
}

void dequeue() {
    if (front == -1 || front > rear) {
        printf("Queue is empty.\n");
        return;
    }

    printf("Deleted element: %d\n", queue[front]);
    front++;

    if (front > rear) {
        front = -1;
        rear = -1;
    }
}

void checkEmpty() {
    if (front == -1)
        printf("Queue is empty.\n");
    else
        printf("Queue is not empty.\n");
}

void checkFull() {
    if (rear == MAX - 1)
        printf("Queue is full.\n");
    else
        printf("Queue is not full.\n");
}

void display() {
    if (front == -1) {
        printf("Queue is empty.\n");
        return;
    }

    printf("Queue: ");

    for (int i = front; i <= rear; i++)
        printf("%d ", queue[i]);

    printf("\n");
}

int main() {
    int choice, data;

    while (1) {
        printf("\n1. Enqueue\n");
        printf("2. Dequeue\n");
        printf("3. Check Empty\n");
        printf("4. Check Full\n");
        printf("5. Traverse\n");
        printf("6. Exit\n");

        printf("Enter choice: ");
        scanf("%d", &choice);

        if (choice == 6)
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
            checkFull();
        }
        else if (choice == 5) {
            display();
        }
        else {
            printf("Invalid choice.\n");
        }
    }

    return 0;
}