"""Student record manager with file persistence and class statistics."""

import csv
import sys
from dataclasses import dataclass
from pathlib import Path


DATA_FILE = Path("student_grades.txt")
EXIT_KEY = "\x1b"


class ExitProgram(Exception):
	"""Raised when the user presses ESC or selects the exit option."""


def calculate_grade(score: float) -> str:
	"""Return the letter grade for a score from 0 through 100."""
	if not 0 <= score <= 100:
		raise ValueError("Score must be between 0 and 100.")
	if score >= 90:
		return "A"
	if score >= 80:
		return "B"
	if score >= 70:
		return "C"
	if score >= 60:
		return "D"
	return "F"


@dataclass
class Student:
	name: str
	student_id: str
	test1: float
	test2: float
	test3: float

	@property
	def average_score(self) -> float:
		return (self.test1 + self.test2 + self.test3) / 3

	@property
	def grade(self) -> str:
		return calculate_grade(self.average_score)


class StudentManager:
	def __init__(self) -> None:
		self.records: dict[str, Student] = {}

	def add_record(self, record: Student) -> None:
		if record.student_id in self.records:
			raise ValueError("A student with that ID already exists.")
		self.records[record.student_id] = record

	def update_record(self, student_id: str, name: str, test1: float,
					 test2: float, test3: float) -> None:
		if student_id not in self.records:
			raise KeyError("Student ID was not found.")
		for score in (test1, test2, test3):
			calculate_grade(score)
		self.records[student_id] = Student(
			name, student_id, test1, test2, test3
		)

	def delete_record(self, student_id: str) -> Student:
		try:
			return self.records.pop(student_id)
		except KeyError as error:
			raise KeyError("Student ID was not found.") from error

	def find_by_name(self, name: str) -> list[Student]:
		query = name.casefold()
		return [record for record in self.all_records()
				if query in record.name.casefold()]

	def all_records(self) -> list[Student]:
		return sorted(self.records.values(), key=lambda record: record.name.casefold())

	def save(self, filename: Path = DATA_FILE) -> None:
		with filename.open("w", newline="") as file:
			writer = csv.writer(file, delimiter="|", lineterminator="\n")
			writer.writerow(("name", "id", "test1", "test2", "test3",
							 "average", "grade"))
			for record in self.all_records():
				writer.writerow((record.name, record.student_id, f"{record.test1:.2f}",
								 f"{record.test2:.2f}", f"{record.test3:.2f}",
								 f"{record.average_score:.2f}",
								 record.grade))

	def load(self, filename: Path = DATA_FILE) -> None:
		if not filename.exists():
			return
		try:
			with filename.open(newline="") as file:
				for row in csv.DictReader(file, delimiter="|"):
					try:
						record = Student(
							row["name"], row["id"], float(row["test1"]),
							float(row["test2"]), float(row["test3"])
						)
						for score in (record.test1, record.test2, record.test3):
							calculate_grade(score)
						if round(float(row["average"]), 2) != round(
							record.average_score, 2
						):
							raise ValueError("Average does not match test scores.")
						if row["grade"] != record.grade:
							raise ValueError("Grade does not match average.")
						self.records[record.student_id] = record
					except (KeyError, ValueError):
						print("Skipped an invalid record in student_grades.txt.")
		except OSError as error:
			print(f"Unable to load student records: {error}")


def read_required(prompt: str) -> str:
	while True:
		value = input(prompt)
		if EXIT_KEY in value:
			raise ExitProgram
		value = value.strip()
		if value:
			return value
		print("This value is required.")


def read_score(prompt: str) -> float:
	while True:
		try:
			score = float(read_required(prompt))
			calculate_grade(score)
			return score
		except ValueError as error:
			print(f"Invalid score: {error}")


def print_table(records: list[Student]) -> None:
	if not records:
		print("No student records available.")
		return
	columns = ("Name", "ID", "Test 1", "Test 2", "Test 3", "Average", "Grade")
	rows = [(record.name, record.student_id, f"{record.test1:.2f}",
		 f"{record.test2:.2f}", f"{record.test3:.2f}",
		 f"{record.average_score:.2f}", record.grade) for record in records]
	widths = [max(len(column), *(len(row[index]) for row in rows))
			  for index, column in enumerate(columns)]
	format_row = " | ".join(f"{{:<{width}}}" for width in widths)
	separator = "-+-".join("-" * width for width in widths)
	print(format_row.format(*columns))
	print(separator)
	for row in rows:
		print(format_row.format(*row))


def show_statistics(manager: StudentManager) -> None:
	records = manager.all_records()
	if not records:
		print("No class statistics available.")
		return
	averages = [record.average_score for record in records]
	print(f"Highest average: {max(averages):.2f}")
	print(f"Lowest average: {min(averages):.2f}")
	print(f"Class average: {sum(averages) / len(averages):.2f}")


def save_records(manager: StudentManager) -> bool:
	try:
		manager.save()
	except OSError as error:
		print(f"Unable to save student records: {error}")
		return False
	return True


def add_student(manager: StudentManager) -> None:
	student_id = read_required("Student ID: ")
	name = read_required("Student name: ")
	scores = [read_score(f"Test {number} score (0-100): ")
			  for number in range(1, 4)]
	try:
		manager.add_record(Student(name, student_id, *scores))
		if save_records(manager):
			print("Student record added and saved successfully.")
		else:
			print("Student record added, but it could not be saved.")
	except ValueError as error:
		print(f"Unable to add record: {error}")


def search_student(manager: StudentManager) -> None:
	name = read_required("Name to search for: ")
	print_table(manager.find_by_name(name))


def print_menu() -> None:
	print("\nStudent Record Manager")
	print("1. Add student")
	print("2. Display all students")
	print("3. Search by name")
	print("4. Display class statistics")
	print("5. Save records")
	print("ESC. Exit")


def read_menu_choice() -> str:
	"""Read one menu key so ESC exits immediately in an interactive terminal."""
	if not sys.stdin.isatty():
		return input("Choose an option (or press ESC): ").strip()
	try:
		import termios
		import tty

		print("Choose an option (or press ESC): ", end="", flush=True)
		settings = termios.tcgetattr(sys.stdin)
		try:
			tty.setcbreak(sys.stdin.fileno())
			choice = sys.stdin.read(1)
		finally:
			termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
		print()
		return choice
	except (ImportError, OSError):
		return input("Choose an option (or press ESC): ").strip()


def main() -> None:
	manager = StudentManager()
	manager.load()
	if manager.records:
		print(f"Loaded {len(manager.records)} student record(s).")
	try:
		while True:
			print_menu()
			choice = read_menu_choice()
			if EXIT_KEY in choice:
				raise ExitProgram
			choice = choice.strip()
			if choice == "1":
				add_student(manager)
			elif choice == "2":
				print_table(manager.all_records())
			elif choice == "3":
				search_student(manager)
			elif choice == "4":
				show_statistics(manager)
			elif choice == "5":
				if save_records(manager):
					print("Student records saved successfully.")
			else:
				print("Choose 1-5 or press ESC to exit.")
	except (ExitProgram, EOFError, KeyboardInterrupt):
		save_records(manager)
		print("Goodbye. Your student records are saved when possible.")


if __name__ == "__main__":
	main()

