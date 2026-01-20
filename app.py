"""
Budgeteer - Personal Finance Application
Main entry point for the Flask application
"""
from app import create_app

# Create the Flask application instance
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
