// Question 1: Write a menu-driven program to perform stack operations such as PUSH, POP, and finding the TOP of the stack.

#include <stdio.h>
#define SIZE 100

int stack[SIZE];
int top = -1;

void push(int value)
{
    if (top == SIZE - 1)
        printf("Stack Overflow!\n");
    else
    {
        top++;
        stack[top] = value;
        printf("Element pushed successfully.\n");
    }
}

void pop()
{
    if (top == -1)
        printf("Stack Underflow!\n");
    else
    {
        printf("Popped element: %d\n", stack[top]);
        top--;
    }
}

void peek()
{
    if (top == -1)
        printf("Stack is empty.\n");
    else
        printf("Top element: %d\n", stack[top]);
}

int main()
{
    int choice, value;

    while (1)
    {
        printf("\n1. PUSH\n2. POP\n3. TOP\n4. EXIT\n");
        printf("Enter your choice: ");
        scanf("%d", &choice);

        switch (choice)
        {
            case 1:
                printf("Enter element: ");
                scanf("%d", &value);
                push(value);
                break;

            case 2:
                pop();
                break;

            case 3:
                peek();
                break;

            case 4:
                return 0;

            default:
                printf("Invalid choice!\n");
        }
    }
}