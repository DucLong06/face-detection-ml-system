import os
import sys
import time
import json
import logging
from typing import List, Dict, Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import KafkaError, TopicAlreadyExistsError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KafkaTestClient:
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        """Initialize Kafka test client"""
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self.consumer = None
        self.admin_client = None

        # Test topic configuration
        self.test_topic = "ingestion-ns -test"
        self.test_messages = [
            {"id": 1, "message": "Hello Kafka!", "timestamp": int(time.time())},
            {"id": 2, "message": "Test message 2", "timestamp": int(time.time())},
            {"id": 3, "message": "Face detection test", "timestamp": int(time.time())}
        ]

    def connect_admin(self) -> bool:
        """Connect to Kafka admin client"""
        try:
            self.admin_client = KafkaAdminClient(
                bootstrap_servers=self.bootstrap_servers,
                client_id='kafka-test-admin'
            )

            # Test connection by getting cluster metadata
            metadata = self.admin_client.describe_cluster()
            logger.info(f"✓ Connected to Kafka cluster: {len(metadata.brokers)} brokers")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to connect admin client: {e}")
            return False

    def connect_producer(self) -> bool:
        """Connect to Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                client_id='kafka-test-producer'
            )

            # Test connection
            self.producer.bootstrap_connected()
            logger.info("✓ Kafka producer connected")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to connect producer: {e}")
            return False

    def connect_consumer(self) -> bool:
        """Connect to Kafka consumer"""
        try:
            self.consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                client_id='kafka-test-consumer',
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='test-group'
            )

            logger.info("✓ Kafka consumer connected")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to connect consumer: {e}")
            return False

    def create_test_topic(self) -> bool:
        """Create test topic"""
        try:
            topic = NewTopic(
                name=self.test_topic,
                num_partitions=3,
                replication_factor=1
            )

            self.admin_client.create_topics([topic])
            logger.info(f"✓ Created test topic: {self.test_topic}")
            return True

        except TopicAlreadyExistsError:
            logger.info(f"✓ Test topic already exists: {self.test_topic}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to create topic: {e}")
            return False

    def list_topics(self) -> List[str]:
        """List all topics"""
        try:
            topics = self.admin_client.list_topics()
            logger.info(f"📋 Available topics: {list(topics)}")
            return list(topics)
        except Exception as e:
            logger.error(f"✗ Failed to list topics: {e}")
            return []

    def produce_test_messages(self) -> bool:
        """Produce test messages"""
        logger.info("📤 Sending test messages...")

        try:
            for i, message in enumerate(self.test_messages):
                # Send message
                future = self.producer.send(
                    self.test_topic,
                    value=message,
                    key=f"test-key-{i}"
                )

                # Wait for acknowledgment
                record_metadata = future.get(timeout=10)
                logger.info(f"✓ Sent message {i+1}: topic={record_metadata.topic}, "
                            f"partition={record_metadata.partition}, offset={record_metadata.offset}")

            # Flush to ensure all messages are sent
            self.producer.flush()
            logger.info("✓ All test messages sent successfully")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to send messages: {e}")
            return False

    def consume_test_messages(self, timeout: int = 30) -> List[Dict]:
        """Consume test messages"""
        logger.info("📥 Consuming test messages...")

        try:
            # Subscribe to test topic
            self.consumer.subscribe([self.test_topic])

            consumed_messages = []
            start_time = time.time()

            while len(consumed_messages) < len(self.test_messages):
                # Check timeout
                if time.time() - start_time > timeout:
                    logger.warning(f"⚠️ Timeout: only consumed {len(consumed_messages)} messages")
                    break

                # Poll for messages
                message_batch = self.consumer.poll(timeout_ms=1000)

                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        consumed_messages.append({
                            'topic': message.topic,
                            'partition': message.partition,
                            'offset': message.offset,
                            'key': message.key.decode('utf-8') if message.key else None,
                            'value': message.value
                        })

                        logger.info(f"✓ Consumed message: {message.value}")

            logger.info(f"✓ Consumed {len(consumed_messages)} messages successfully")
            return consumed_messages

        except Exception as e:
            logger.error(f"✗ Failed to consume messages: {e}")
            return []

    def get_topic_info(self, topic: str) -> Dict:
        """Get topic information"""
        try:
            # Get topic metadata
            topic_metadata = self.admin_client.describe_topics([topic])

            if topic in topic_metadata:
                topic_info = topic_metadata[topic]
                return {
                    'topic': topic,
                    'partitions': len(topic_info.partitions),
                    'partition_info': [
                        {
                            'partition': p.partition,
                            'leader': p.leader,
                            'replicas': p.replicas,
                            'isr': p.isr
                        } for p in topic_info.partitions
                    ]
                }
            else:
                return {}

        except Exception as e:
            logger.error(f"✗ Failed to get topic info: {e}")
            return {}

    def cleanup_test_topic(self) -> bool:
        """Delete test topic"""
        try:
            self.admin_client.delete_topics([self.test_topic])
            logger.info(f"✓ Deleted test topic: {self.test_topic}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to delete topic: {e}")
            return False

    def close_connections(self):
        """Close all connections"""
        if self.producer:
            self.producer.close()
        if self.consumer:
            self.consumer.close()
        if self.admin_client:
            self.admin_client.close()

        logger.info("✓ All connections closed")

    def run_full_test(self) -> bool:
        """Run complete Kafka test"""
        logger.info("🚀 Starting Kafka full test...")

        success = True

        # Step 1: Connect admin client
        if not self.connect_admin():
            return False

        # Step 2: List existing topics
        self.list_topics()

        # Step 3: Create test topic
        if not self.create_test_topic():
            success = False

        # Step 4: Get topic info
        topic_info = self.get_topic_info(self.test_topic)
        if topic_info:
            logger.info(f"📊 Topic info: {topic_info}")

        # Step 5: Connect producer
        if not self.connect_producer():
            success = False

        # Step 6: Send messages
        if success and not self.produce_test_messages():
            success = False

        # Step 7: Connect consumer
        if not self.connect_consumer():
            success = False

        # Step 8: Consume messages
        if success:
            consumed = self.consume_test_messages()
            if len(consumed) != len(self.test_messages):
                logger.warning(f"⚠️ Expected {len(self.test_messages)} messages, got {len(consumed)}")
                success = False

        # Cleanup
        self.close_connections()

        if success:
            logger.info("🎉 Kafka test completed successfully!")
        else:
            logger.error("❌ Kafka test failed!")

        return success


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Test Kafka connectivity')
    parser.add_argument('--bootstrap-servers', default='localhost:9092',
                        help='Kafka bootstrap servers')
    parser.add_argument('--port-forward', action='store_true',
                        help='Use port forwarding (kubectl port-forward)')
    parser.add_argument('--cleanup', action='store_true',
                        help='Clean up test topic after test')

    args = parser.parse_args()

    # If port-forward is requested, start it
    if args.port_forward:
        logger.info("Starting port forward to Kafka...")
        os.system("kubectl port-forward service/kafka-cluster 9092:9092 -n ingestion-ns  &")
        time.sleep(5)  # Wait for port forward to establish

    # Run test
    client = KafkaTestClient(args.bootstrap_servers)

    try:
        success = client.run_full_test()

        # Cleanup if requested
        if args.cleanup and success:
            client.cleanup_test_topic()

        # Exit code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        client.close_connections()
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        client.close_connections()
        sys.exit(1)


if __name__ == "__main__":
    main()
