import argparse
import subprocess
import sys
from modules import clearTerminal

def main():
    parser = argparse.ArgumentParser(description="Launch CLI or GUI version of the program.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-cli', action='store_true', help="Run the CLI version")
    group.add_argument('-gui', action='store_true', help="Run the GUI version (Streamlit)")

    args = parser.parse_args()

    # If no argument is provided, prompt the user
    if not any(vars(args).values()):
        choice = input("No flag provided. Type 'cli' for command line or 'gui' for GUI: ").strip().lower()
        if choice == "cli":
            args.cli = True
        elif choice == "gui":
            args.gui = True
        else:
            print("Invalid input. Please use 'cli' or 'gui'.")
            sys.exit(1)

    if args.cli:
        subprocess.run([sys.executable, "cli.py"])

    elif args.gui:
        clearTerminal()
        subprocess.run(["streamlit", "run", "gui.py"])

if __name__ == "__main__":
    main()
