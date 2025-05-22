#!/bin/bash

echo "🚀 Starting Hybrid Confluent Platform (Fixed)..."

# Stop previous containers
docker-compose down 2>/dev/null

# Kill existing port forwards
pkill -f "kubectl port-forward" 2>/dev/null

# Get Kafka password
export CLIENT_PASSWORD=$(kubectl get secret kafka-user-passwords -n ingestion-ns -o jsonpath='{.data.client-passwords}' | base64 --decode)
echo "📋 Client Password: $CLIENT_PASSWORD"

# Verify Kafka is running
echo "🔍 Checking Kafka status..."
kubectl get pods -n ingestion-ns | grep kafka

# Create client config in Kafka pod
echo "📝 Creating SASL config..."
kubectl exec -it kafka-controller-0 -n ingestion-ns -- bash -c "
cat > /tmp/client.properties << EOF
security.protocol=SASL_PLAINTEXT
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username=\"user1\" password=\"$CLIENT_PASSWORD\";
EOF
"

# Test Kafka connectivity from pod
echo "🧪 Testing Kafka from pod..."
kubectl exec -it kafka-controller-0 -n ingestion-ns -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --command-config /tmp/client.properties \
  --list

# Port forward with proper binding
echo "🔗 Setting up port forward..."
kubectl port-forward --address 0.0.0.0 svc/kafka 9092:9092 -n ingestion-ns &
PORT_FORWARD_PID=$!

# Wait for port forward to be ready
echo "⏳ Waiting for port forward..."
sleep 10

# Test port forward
echo "🧪 Testing port forward..."
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/localhost/9092' && echo "✅ Port 9092 is open" || echo "❌ Port 9092 is not accessible"

# Start Docker services
echo "🐳 Starting Docker services..."
CLIENT_PASSWORD=$CLIENT_PASSWORD docker compose up -d

echo "✅ Services started! Checking status..."
docker-compose ps

echo "🎛️ Control Center: http://localhost:9021"
echo "🔧 Schema Registry: http://localhost:8081"
echo "🔌 Kafka Connect: http://localhost:8083"
echo "🗄️ TimescaleDB: localhost:5432"

# Save PID for cleanup
echo $PORT_FORWARD_PID > /tmp/kafka-port-forward.pid