/*
Using program 1, write a program to find the student having the highest mark. 
*/


#include <stdio.h>
#include <string.h>

#define MAX_STUDENTS 5
#define NAME_SIZE 50
#define ROLLNO_SIZE 20

struct Student {
    char name[NAME_SIZE];
    char rollNo[ROLLNO_SIZE];
    int marks;
    char grade;
};

void readLine(char *buf, int size) {
    if (fgets(buf, size, stdin) != NULL) {
        buf[strcspn(buf, "\n")] = '\0';
    } else {
        buf[0] = '\0';
    }
}

void flushInput(void) {
    int c;
    while ((c = getchar()) != '\n' && c != EOF) { }
}

int readInt(const char *prompt) {
    int value;
    while (1) {
        printf("%s", prompt);
        if (scanf("%d", &value) == 1) {
            flushInput();
            return value;
        }
        printf("Invalid number, please try again.\n");
        flushInput();
    }
}

void computeGrade(struct Student *s) {
    if (s->marks >= 90)      s->grade = 'A';
    else if (s->marks >= 80) s->grade = 'B';
    else if (s->marks >= 70) s->grade = 'C';
    else if (s->marks >= 60) s->grade = 'D';
    else                     s->grade = 'F';
}

void displayAll(const struct Student *students, int count) {
    if (count == 0) {
        printf("No records found.\n");
        return;
    }
    printf("\n%-20s %-14s %-6s %-6s\n", "Name", "Roll No", "Marks", "Grade");
    printf("------------------------------------------------------------\n");
    for (int i = 0; i < count; i++) {
        printf("%-20s %-14s %-6d %-6c\n",
               students[i].name,
               students[i].rollNo,
               students[i].marks,
               students[i].grade);
    }
    printf("------------------------------------------------------------\n");
}

/* Finds and returns the index of the student with the highest marks. */
int findHighest(const struct Student *students, int count) {
    int maxIdx = 0;
    for (int i = 1; i < count; i++) {
        if (students[i].marks > students[maxIdx].marks)
            maxIdx = i;
    }
    return maxIdx;
}

int main(void) {
    struct Student students[MAX_STUDENTS];
    int count = 0;

    printf("Enter details for %d students:\n", MAX_STUDENTS);
    for (int i = 0; i < MAX_STUDENTS; i++) {
        printf("\nStudent %d:\n", i + 1);
        printf("Enter name: ");
        readLine(students[i].name, NAME_SIZE);
        printf("Enter roll number: ");
        readLine(students[i].rollNo, ROLLNO_SIZE);
        students[i].marks = readInt("Enter marks: ");
        computeGrade(&students[i]);
        count++;
    }

    displayAll(students, count);

    int topIdx = findHighest(students, count);
    printf("\nStudent with the highest marks:\n");
    printf("Name: %s\nRoll No: %s\nMarks: %d\nGrade: %c\n",
           students[topIdx].name,
           students[topIdx].rollNo,
           students[topIdx].marks,
           students[topIdx].grade);

    return 0;
}