# -*- coding: utf-8 -*-

# This is the main entry point for the application.
# It creates an instance of the app and runs it.

from .app import TheOrangeDiskApp

def main():
    """Initializes and runs the application."""
    try:
        app = TheOrangeDiskApp()
        app.run()
    except Exception as e:
        # A top-level crash handler
        print("="*50)
        print("!!! A FATAL, UNHANDLED ERROR OCCURRED !!!")
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*50)
        # Keep the console open for a moment so the user can see the error
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
