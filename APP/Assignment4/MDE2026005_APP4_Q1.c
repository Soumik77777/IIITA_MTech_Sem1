/*
Write  a  C  program  to  create  a  grade  sheet using structures containing names, roll 
numbers, marks, and grades of 5 students. The program should be able to insert a new 
record, delete it, and modify it based on user input, i.e., menu-driven. 
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
        buf[strcspn(buf, "\n")] = '\0';   /* strip trailing newline if present */
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

int findStudent(const struct Student *students, int count, const char *rollNo) {
    for (int i = 0; i < count; i++) {
        if (strcmp(students[i].rollNo, rollNo) == 0)
            return i;
    }
    return -1;
}

int main(void) {
    struct Student students[MAX_STUDENTS];
    int count = 0;
    int choice, idx, marks;
    char rollNo[ROLLNO_SIZE];

    while (1) {
        printf("\n=== Grade Sheet Menu ===\n");
        printf("1. Insert Record\n");
        printf("2. Delete Record\n");
        printf("3. Modify Record\n");
        printf("4. Display All\n");
        printf("5. Exit\n");

        choice = readInt("Enter choice: ");

        switch (choice) {
            case 1:
                if (count >= MAX_STUDENTS) {
                    printf("Grade sheet is full (max %d students).\n", MAX_STUDENTS);
                    break;
                }
                printf("Enter name: ");
                readLine(students[count].name, NAME_SIZE);
                printf("Enter roll number (e.g. MDE2026005): ");
                readLine(students[count].rollNo, ROLLNO_SIZE);
                marks = readInt("Enter marks: ");
                students[count].marks = marks;
                computeGrade(&students[count]);
                count++;
                printf("Record inserted successfully.\n");
                break;

            case 2:
                if (count == 0) {
                    printf("No records to delete.\n");
                    break;
                }
                printf("Enter roll number to delete: ");
                readLine(rollNo, ROLLNO_SIZE);
                idx = findStudent(students, count, rollNo);
                if (idx == -1) {
                    printf("Student with roll number %s not found.\n", rollNo);
                    break;
                }
                for (int i = idx; i < count - 1; i++)
                    students[i] = students[i + 1];
                count--;
                printf("Record deleted successfully.\n");
                break;

            case 3:
                if (count == 0) {
                    printf("No records to modify.\n");
                    break;
                }
                printf("Enter roll number to modify: ");
                readLine(rollNo, ROLLNO_SIZE);
                idx = findStudent(students, count, rollNo);
                if (idx == -1) {
                    printf("Student with roll number %s not found.\n", rollNo);
                    break;
                }
                printf("Enter new name: ");
                readLine(students[idx].name, NAME_SIZE);
                marks = readInt("Enter new marks: ");
                students[idx].marks = marks;
                computeGrade(&students[idx]);
                printf("Record modified successfully.\n");
                break;

            case 4:
                displayAll(students, count);
                break;

            case 5:
                printf("Exiting.\n");
                return 0;

            default:
                printf("Invalid choice. Try again.\n");
                break;
        }
    }

    return 0;
}