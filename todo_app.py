#!/usr/bin/env python3
"""
Complete TODO List Application with SQLite Database
"""

import argparse
import sqlite3
from datetime import datetime
from enum import Enum
from typing import List, Optional

from tabulate import tabulate


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class Status(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TodoDatabase:
    def __init__(self, db_path: str = "todos.db"):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Establish connection to SQLite database"""
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 2,
                status TEXT DEFAULT 'pending',
                category TEXT,
                due_date TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT,
                created_at TEXT NOT NULL
            )
        """
        )

        self.connection.commit()

    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()


class TodoManager:
    def __init__(self, db: TodoDatabase):
        self.db = db

    def add_todo(
        self,
        title: str,
        description: str = None,
        priority: int = 2,
        category: str = None,
        due_date: str = None,
    ) -> int:
        """Add a new TODO item"""
        now = datetime.now().isoformat()

        self.db.cursor.execute(
            """
            INSERT INTO todos (title, description, priority, status, category, due_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                title,
                description,
                priority,
                Status.PENDING.value,
                category,
                due_date,
                now,
                now,
            ),
        )

        self.db.connection.commit()
        return self.db.cursor.lastrowid

    def list_todos(
        self, status: str = None, category: str = None, sort_by: str = "created_at"
    ) -> List[sqlite3.Row]:
        """List TODO items with optional filters"""
        query = "SELECT * FROM todos WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += f" ORDER BY {sort_by} DESC"

        self.db.cursor.execute(query, params)
        return self.db.cursor.fetchall()

    def get_todo(self, todo_id: int) -> Optional[sqlite3.Row]:
        """Get a specific TODO item"""
        self.db.cursor.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
        return self.db.cursor.fetchone()

    def update_todo(self, todo_id: int, **kwargs) -> bool:
        """Update a TODO item"""
        todo = self.get_todo(todo_id)
        if not todo:
            return False

        allowed_fields = [
            "title",
            "description",
            "priority",
            "status",
            "category",
            "due_date",
        ]
        updates = []
        values = []

        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                updates.append(f"{field} = ?")
                values.append(value)

        if not updates:
            return False

        # Add updated_at timestamp
        updates.append("updated_at = ?")
        values.append(datetime.now().isoformat())

        # Check if status changed to completed
        if "status" in kwargs and kwargs["status"] == Status.COMPLETED.value:
            updates.append("completed_at = ?")
            values.append(datetime.now().isoformat())

        values.append(todo_id)

        query = f"UPDATE todos SET {', '.join(updates)} WHERE id = ?"
        self.db.cursor.execute(query, values)
        self.db.connection.commit()

        return self.db.cursor.rowcount > 0

    def delete_todo(self, todo_id: int) -> bool:
        """Delete a TODO item"""
        self.db.cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        self.db.connection.commit()
        return self.db.cursor.rowcount > 0

    def mark_complete(self, todo_id: int) -> bool:
        """Mark a TODO item as completed"""
        return self.update_todo(todo_id, status=Status.COMPLETED.value)

    def add_category(self, name: str, color: str = None) -> int:
        """Add a new category"""
        try:
            now = datetime.now().isoformat()
            self.db.cursor.execute(
                "INSERT INTO categories (name, color, created_at) VALUES (?, ?, ?)",
                (name, color, now),
            )
            self.db.connection.commit()
            return self.db.cursor.lastrowid
        except sqlite3.IntegrityError:
            return -1

    def list_categories(self) -> List[sqlite3.Row]:
        """List all categories"""
        self.db.cursor.execute("SELECT * FROM categories ORDER BY name")
        return self.db.cursor.fetchall()

    def get_statistics(self) -> dict:
        """Get TODO statistics"""
        stats = {}

        # Total todos
        self.db.cursor.execute("SELECT COUNT(*) as count FROM todos")
        stats["total"] = self.db.cursor.fetchone()["count"]

        # By status
        self.db.cursor.execute(
            """
            SELECT status, COUNT(*) as count
            FROM todos
            GROUP BY status
        """
        )
        stats["by_status"] = {
            row["status"]: row["count"] for row in self.db.cursor.fetchall()
        }

        # By priority
        self.db.cursor.execute(
            """
            SELECT priority, COUNT(*) as count
            FROM todos
            WHERE status != 'completed'
            GROUP BY priority
        """
        )
        stats["by_priority"] = {
            row["priority"]: row["count"] for row in self.db.cursor.fetchall()
        }

        # Overdue tasks
        self.db.cursor.execute(
            """
            SELECT COUNT(*) as count
            FROM todos
            WHERE status != 'completed'
            AND due_date IS NOT NULL
            AND due_date < datetime('now')
        """
        )
        stats["overdue"] = self.db.cursor.fetchone()["count"]

        return stats


class TodoCLI:
    def __init__(self):
        self.db = TodoDatabase()
        self.manager = TodoManager(self.db)

    def format_todo(self, todo: sqlite3.Row) -> dict:
        """Format a todo for display"""
        priority_map = {1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}

        return {
            "ID": todo["id"],
            "Title": todo["title"][:50],
            "Priority": priority_map.get(todo["priority"], "Medium"),
            "Status": todo["status"].replace("_", " ").title(),
            "Category": todo["category"] or "-",
            "Due Date": todo["due_date"][:10] if todo["due_date"] else "-",
            "Created": todo["created_at"][:10],
        }

    def display_todos(self, todos: List[sqlite3.Row]):
        """Display todos in a formatted table"""
        if not todos:
            print("No todos found.")
            return

        data = [self.format_todo(todo) for todo in todos]
        print(tabulate(data, headers="keys", tablefmt="grid"))

    def display_todo_detail(self, todo: sqlite3.Row):
        """Display detailed view of a single todo"""
        if not todo:
            print("Todo not found.")
            return

        priority_map = {1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}

        print("\n" + "=" * 60)
        print(f"TODO #{todo['id']}")
        print("=" * 60)
        print(f"Title:       {todo['title']}")
        print(f"Description: {todo['description'] or 'No description'}")
        print(f"Priority:    {priority_map.get(todo['priority'], 'Medium')}")
        print(f"Status:      {todo['status'].replace('_', ' ').title()}")
        print(f"Category:    {todo['category'] or 'Uncategorized'}")
        print(f"Due Date:    {todo['due_date'] or 'No due date'}")
        print(f"Created:     {todo['created_at']}")
        print(f"Updated:     {todo['updated_at']}")
        if todo["completed_at"]:
            print(f"Completed:   {todo['completed_at']}")
        print("=" * 60 + "\n")

    def display_statistics(self):
        """Display statistics"""
        stats = self.manager.get_statistics()
        priority_map = {1: "Low", 2: "Medium", 3: "High", 4: "Urgent"}

        print("\n" + "=" * 60)
        print("TODO STATISTICS")
        print("=" * 60)
        print(f"Total TODOs: {stats['total']}")
        print("\nBy Status:")
        for status, count in stats["by_status"].items():
            print(f"  {status.replace('_', ' ').title()}: {count}")
        print("\nBy Priority (Active):")
        for priority, count in stats["by_priority"].items():
            print(f"  {priority_map.get(priority, 'Unknown')}: {count}")
        print(f"\nOverdue Tasks: {stats['overdue']}")
        print("=" * 60 + "\n")

    def run(self):
        """Main CLI loop"""
        parser = argparse.ArgumentParser(description="TODO List Application")
        subparsers = parser.add_subparsers(dest="command", help="Commands")

        # Add command
        add_parser = subparsers.add_parser("add", help="Add a new todo")
        add_parser.add_argument("title", help="Todo title")
        add_parser.add_argument("-d", "--description", help="Todo description")
        add_parser.add_argument(
            "-p",
            "--priority",
            type=int,
            choices=[1, 2, 3, 4],
            default=2,
            help="Priority (1=Low, 2=Medium, 3=High, 4=Urgent)",
        )
        add_parser.add_argument("-c", "--category", help="Category")
        add_parser.add_argument("--due", help="Due date (YYYY-MM-DD)")

        # List command
        list_parser = subparsers.add_parser("list", help="List todos")
        list_parser.add_argument(
            "-s",
            "--status",
            choices=["pending", "in_progress", "completed", "cancelled"],
            help="Filter by status",
        )
        list_parser.add_argument("-c", "--category", help="Filter by category")
        list_parser.add_argument(
            "--sort",
            choices=["created_at", "updated_at", "priority", "due_date"],
            default="created_at",
            help="Sort by field",
        )

        # Show command
        show_parser = subparsers.add_parser("show", help="Show todo details")
        show_parser.add_argument("id", type=int, help="Todo ID")

        # Update command
        update_parser = subparsers.add_parser("update", help="Update a todo")
        update_parser.add_argument("id", type=int, help="Todo ID")
        update_parser.add_argument("-t", "--title", help="New title")
        update_parser.add_argument("-d", "--description", help="New description")
        update_parser.add_argument(
            "-p", "--priority", type=int, choices=[1, 2, 3, 4], help="New priority"
        )
        update_parser.add_argument(
            "-s",
            "--status",
            choices=["pending", "in_progress", "completed", "cancelled"],
            help="New status",
        )
        update_parser.add_argument("-c", "--category", help="New category")
        update_parser.add_argument("--due", help="New due date (YYYY-MM-DD)")

        # Complete command
        complete_parser = subparsers.add_parser(
            "complete", help="Mark todo as completed"
        )
        complete_parser.add_argument("id", type=int, help="Todo ID")

        # Delete command
        delete_parser = subparsers.add_parser("delete", help="Delete a todo")
        delete_parser.add_argument("id", type=int, help="Todo ID")

        # Category commands
        category_parser = subparsers.add_parser("category", help="Manage categories")
        category_subparsers = category_parser.add_subparsers(dest="category_command")

        cat_add = category_subparsers.add_parser("add", help="Add a category")
        cat_add.add_argument("name", help="Category name")
        cat_add.add_argument("-c", "--color", help="Category color")

        category_subparsers.add_parser("list", help="List categories")

        # Stats command
        subparsers.add_parser("stats", help="Show statistics")

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            return

        try:
            if args.command == "add":
                todo_id = self.manager.add_todo(
                    args.title, args.description, args.priority, args.category, args.due
                )
                print(f"✅ Todo added successfully! (ID: {todo_id})")

            elif args.command == "list":
                todos = self.manager.list_todos(args.status, args.category, args.sort)
                self.display_todos(todos)

            elif args.command == "show":
                todo = self.manager.get_todo(args.id)
                self.display_todo_detail(todo)

            elif args.command == "update":
                updates = {}
                if args.title:
                    updates["title"] = args.title
                if args.description:
                    updates["description"] = args.description
                if args.priority:
                    updates["priority"] = args.priority
                if args.status:
                    updates["status"] = args.status
                if args.category:
                    updates["category"] = args.category
                if args.due:
                    updates["due_date"] = args.due

                if self.manager.update_todo(args.id, **updates):
                    print(f"✅ Todo #{args.id} updated successfully!")
                else:
                    print(f"❌ Failed to update todo #{args.id}")

            elif args.command == "complete":
                if self.manager.mark_complete(args.id):
                    print(f"✅ Todo #{args.id} marked as completed!")
                else:
                    print(f"❌ Failed to complete todo #{args.id}")

            elif args.command == "delete":
                if self.manager.delete_todo(args.id):
                    print(f"✅ Todo #{args.id} deleted successfully!")
                else:
                    print(f"❌ Failed to delete todo #{args.id}")

            elif args.command == "category":
                if args.category_command == "add":
                    cat_id = self.manager.add_category(args.name, args.color)
                    if cat_id > 0:
                        print(f"✅ Category '{args.name}' added successfully!")
                    else:
                        print(f"❌ Category '{args.name}' already exists!")

                elif args.category_command == "list":
                    categories = self.manager.list_categories()
                    if categories:
                        print("\nCategories:")
                        for cat in categories:
                            color_info = f" ({cat['color']})" if cat["color"] else ""
                            print(f"  - {cat['name']}{color_info}")
                    else:
                        print("No categories found.")

            elif args.command == "stats":
                self.display_statistics()

        except Exception as e:
            print(f"❌ Error: {e}")

        finally:
            self.db.close()


def main():
    cli = TodoCLI()
    cli.run()


if __name__ == "__main__":
    main()
