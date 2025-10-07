from app import create_app

app = create_app()

if __name__ == "__main__":
    print("🚀 Iniciando Flask...")
    app.run(debug=True)
