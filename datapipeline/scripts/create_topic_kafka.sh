CLIENT_PASSWORD=$(kubectl get secret kafka-user-passwords -n ingestion-ns -o jsonpath='{.data.client-passwords}' | base64 --decode)
echo "Client Password: $CLIENT_PASSWORD"

# Create Kafka client properties file
kubectl exec -it kafka-controller-0  -n ingestion-ns -- bash -c "
cat > /tmp/client.properties << 'EOF'
security.protocol=SASL_PLAINTEXT
sasl.mechanism=PLAIN
sasl.jaas.config=org.apache.kafka.common.security.plain.PlainLoginModule required username=\"user1\" password=\"$CLIENT_PASSWORD\";
EOF"

# Create topics for face detection pipeline
echo "📂 Creating Kafka topics for face detection..."

# Topic 1: Face Images Metadata (main data stream)
kubectl exec -it kafka-controller-0  -n ingestion-ns -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --command-config /tmp/client.properties \
  --create --topic face-images-metadata \
  --partitions 3 --replication-factor 1 \
  --config cleanup.policy=compact \
  --config retention.ms=86400000

# Topic 2: Face Annotations Stream (processed annotations)  
kubectl exec -it kafka-controller-0  -n ingestion-ns -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --command-config /tmp/client.properties \
  --create --topic face-annotations-stream \
  --partitions 3 --replication-factor 1 \
  --config retention.ms=604800000

# Topic 3: Data Quality Events (validation results)
kubectl exec -it kafka-controller-0  -n ingestion-ns -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --command-config /tmp/client.properties \
  --create --topic data-quality-events \
  --partitions 1 --replication-factor 1 \
  --config retention.ms=2592000000

# Topic 4: Processing Status (pipeline status updates)
kubectl exec -it kafka-controller-0  -n ingestion-ns -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --command-config /tmp/client.properties \
  --create --topic processing-status \
  --partitions 1 --replication-factor 1 \
  --config retention.ms=259200000

# Verify topics created
echo "📋 Verifying created topics..."
kubectl exec -it kafka-controller-0  -n ingestion-ns -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --command-config /tmp/client.properties \
  --list | grep -E "(face-|data-quality|processing-status)"

# Get topic details
echo "📊 Topic configurations:"
kubectl exec -it kafka-controller-0  -n ingestion-ns -- kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --command-config /tmp/client.properties \
  --describe --topic face-images-metadata