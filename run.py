"""Start the app locally:  python run.py   then open http://localhost:5000"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
