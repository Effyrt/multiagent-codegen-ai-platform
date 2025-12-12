#!/bin/bash

echo "�� Starting CodeGen AI..."

# Start Airflow
echo "Starting Airflow..."
docker-compose -f docker-compose-airflow.yml up -d

# Wait for Airflow
sleep 10

echo ""
echo "✅ Airflow: http://localhost:8082"
echo "📝 Now run in separate terminals:"
echo "   Terminal 1: cd backend && python main.py"
echo "   Terminal 2: cd frontend && npm run dev"
echo ""
echo "Then access:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8001"
echo "   Airflow:  http://localhost:8082"
