#!/bin/bash

echo "�� Starting CodeGen AI Development Environment..."
echo ""

# Start Airflow
echo "📊 Starting Airflow..."
docker-compose -f docker-compose-airflow.yml up -d

# Wait for Airflow to initialize
echo "⏳ Waiting for Airflow to initialize..."
sleep 10

echo ""
echo "✅ Services Starting!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 Airflow UI:     http://localhost:8082"
echo "   (username: admin, password: admin)"
echo ""
echo "📝 Next Steps:"
echo "   Terminal 1: cd backend && python main.py"
echo "   Terminal 2: cd frontend && npm run dev"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "After starting backend and frontend:"
echo "   🎨 Frontend:  http://localhost:3000"
echo "   🔌 Backend:   http://localhost:8001"
echo "   📊 Airflow:   http://localhost:8082"
echo ""
echo "🌍 Production URLs:"
echo "   Frontend: https://codegen-q0xe6wp31-omraut04052002-gmailcoms-projects.vercel.app"
echo "   Backend:  https://codegen-backend-428108273170.us-central1.run.app"
echo ""
