#!/usr/bin/env python
"""
SQLite Interactive Helper
Run this to practice SQLite commands interactively
"""

import sqlite3
import sys
import os
from pathlib import Path


class SQLiteHelper:
    """Interactive SQLite helper for learning"""

    def __init__(self, db_name='practice.db'):
        self.db_name = db_name
        self.conn = None
        self.setup_database()

    def setup_database(self):
        """Create connection with helpful settings"""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        print(f"✅ Connected to database: {self.db_name}")

    def execute_query(self, query):
        """Execute a query and return results"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)

            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                return results
            else:
                self.conn.commit()
                return f"✅ Query executed. Rows affected: {cursor.rowcount}"

        except sqlite3.Error as e:
            return f"❌ Error: {e}"

    def display_results(self, results):
        """Display query results in a nice format"""
        if isinstance(results, str):
            print(results)
            return

        if not results:
            print("No results returned.")
            return

        # Get column names
        columns = results[0].keys()
        col_widths = [max(len(col), 15) for col in columns]

        # Print header
        header = " | ".join(col.ljust(width) for col, width in zip(columns, col_widths))
        print(header)
        print("-" * len(header))

        # Print rows
        for row in results:
            row_str = " | ".join(
                str(row[col]).ljust(width) for col, width in zip(columns, col_widths)
            )
            print(row_str)

        print(f"\nTotal rows: {len(results)}")

    def list_tables(self):
        """List all tables in database"""
        query = """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        results = self.execute_query(query)

        if results:
            print("\n📋 Tables in database:")
            for row in results:
                print(f"  • {row['name']}")
        else:
            print("\nNo tables found. Create one with CREATE TABLE!")

    def show_schema(self, table_name):
        """Show schema for a table"""
        query = f"PRAGMA table_info({table_name})"
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            results = cursor.fetchall()

            if results:
                print(f"\n📊 Schema for table '{table_name}':")
                print("-" * 70)
                for col in results:
                    pk = " (PRIMARY KEY)" if col[5] else ""
                    not_null = " NOT NULL" if col[3] else ""
                    default = f" DEFAULT {col[4]}" if col[4] else ""
                    print(f"  {col[1]:20} {col[2]:10}{not_null}{default}{pk}")
            else:
                print(f"❌ Table '{table_name}' not found")

        except sqlite3.Error as e:
            print(f"❌ Error: {e}")

    def run_file(self, filename):
        """Execute SQL from a file"""
        filepath = Path(filename)

        if not filepath.exists():
            print(f"❌ File not found: {filename}")
            return

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sql_script = f.read()

            self.conn.executescript(sql_script)
            self.conn.commit()
            print(f"✅ Executed SQL from {filename}")

        except sqlite3.Error as e:
            print(f"❌ Error executing file: {e}")

    def show_help(self):
        """Show help message"""
        help_text = """
╔═══════════════════════════════════════════════════════════════╗
║                  SQLite Interactive Helper                     ║
╚═══════════════════════════════════════════════════════════════╝

Commands:
  .help              Show this help message
  .tables            List all tables
  .schema [table]    Show schema for table
  .run [file.sql]    Execute SQL file
  .quit or .exit     Exit the program
  .clear             Clear screen

SQL Commands:
  Just type any SQL command and press Enter!

Examples:
  CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
  INSERT INTO users (name) VALUES ('Alice');
  SELECT * FROM users;
  UPDATE users SET name = 'Bob' WHERE id = 1;
  DELETE FROM users WHERE id = 1;

Tips:
  • SQL commands can span multiple lines
  • End commands with semicolon (;)
  • Use .tables to see what tables exist
  • Use .schema tablename to see table structure

Current database: {db_name}
        """.format(db_name=self.db_name)
        print(help_text)

    def clear_screen(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def run_interactive(self):
        """Run interactive mode"""
        print("\n" + "=" * 70)
        print("SQLite Interactive Helper - Learn SQLite by Doing!")
        print("=" * 70)
        print(f"Database: {self.db_name}")
        print("Type .help for help, .quit to exit\n")

        buffer = []

        while True:
            try:
                if buffer:
                    prompt = "...> "
                else:
                    prompt = "sql> "

                line = input(prompt).strip()

                # Handle special commands
                if not buffer and line.startswith('.'):
                    cmd = line.split()[0].lower()
                    args = line.split()[1:] if len(line.split()) > 1 else []

                    if cmd in ['.quit', '.exit']:
                        print("\n👋 Goodbye!")
                        break

                    elif cmd == '.help':
                        self.show_help()

                    elif cmd == '.tables':
                        self.list_tables()

                    elif cmd == '.schema':
                        if args:
                            self.show_schema(args[0])
                        else:
                            print("Usage: .schema [table_name]")

                    elif cmd == '.run':
                        if args:
                            self.run_file(args[0])
                        else:
                            print("Usage: .run [filename.sql]")

                    elif cmd == '.clear':
                        self.clear_screen()

                    else:
                        print(f"Unknown command: {cmd}")
                        print("Type .help for available commands")

                    continue

                # Handle SQL commands
                if line:
                    buffer.append(line)

                # Check if command is complete (ends with ;)
                if buffer and buffer[-1].endswith(';'):
                    query = ' '.join(buffer)
                    buffer = []

                    results = self.execute_query(query)
                    self.display_results(results)
                    print()

            except KeyboardInterrupt:
                print("\n\nUse .quit to exit")
                buffer = []

            except EOFError:
                print("\n\n👋 Goodbye!")
                break

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def main():
    """Main function"""
    # Check for command line arguments
    db_name = sys.argv[1] if len(sys.argv) > 1 else 'practice.db'

    helper = SQLiteHelper(db_name)

    try:
        helper.run_interactive()
    finally:
        helper.close()


if __name__ == "__main__":
    main()
