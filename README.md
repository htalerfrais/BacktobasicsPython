For development testing, you should run everything from the project/ folder
run the app with uvicorn using : uvicorn src.main:app --host 0.0.0.0 --port 5000

## Stress test on the API from outside the container: 
locust -f project/tests/load/locustfile.py --host=http://localhost:5000

go on locust : http://localhost:8089

go on Flower : http://localhost:5555