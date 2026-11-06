import uvicorn

if __name__ == "__main__":
    # env_file: carica SECRET_KEY e le altre variabili dal file .env (vedi .env.example)
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, env_file=".env")
