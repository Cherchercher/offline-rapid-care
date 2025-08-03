#!/bin/bash

echo "🧹 Clearing offline storage..."

# Clear uploads directory
if [ -d "uploads" ]; then
    rm -rf uploads/*
    echo "✅ Cleared uploads directory"
else
    echo "ℹ️  Uploads directory doesn't exist"
fi

# Clear offload directory
if [ -d "offload" ]; then
    rm -rf offload/*
    echo "✅ Cleared offload directory"
else
    echo "ℹ️  Offload directory doesn't exist"
fi

# Clear database (if it exists)
if [ -f "rapidcare_offline.db" ]; then
    python3 clear_offline_storage.py
else
    echo "ℹ️  Database file doesn't exist"
fi

echo "🎉 Offline storage cleared!"
echo "📁 All stored files and tasks have been removed" 