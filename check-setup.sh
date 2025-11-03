#!/bin/bash

echo "🔍 Checking SmartPDF Shrinker Setup..."
echo ""

# Check if required files exist
files=(
  "docker-compose.yml"
  "nginx.conf"
  ".env"
  "backend/Dockerfile"
  "backend/requirements.txt"
  "backend/app/main.py"
  "frontend/Dockerfile"
  "frontend/package.json"
  "frontend/src/app/page.tsx"
)

missing=0
for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    echo "✅ $file"
  else
    echo "❌ $file"
    missing=$((missing+1))
  fi
done

echo ""
if [ $missing -eq 0 ]; then
  echo "✅ All required files present!"
  echo ""
  echo "To start the application:"
  echo "  docker-compose up --build"
  exit 0
else
  echo "❌ $missing file(s) missing!"
  exit 1
fi
