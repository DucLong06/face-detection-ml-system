"""
Face Detection Streaming Pipeline
Simplified approach: Auto-create topics + Stream data + Consume messages
"""
import json
import os
import time
import threading
from datetime import datetime, timezone
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FaceDetectionStreaming:
    def __init__(self):
        self.kafka_config = self.load_kafka_config()
        self.producer = self.create_producer()
        self.running = True
        self.stats = {
            'images_sent': 0,
            'annotations_sent': 0,
            'messages_consumed': 0,
            'total_faces': 0
        }
        
    def load_kafka_config(self):
        """Load Kafka configuration - simplified"""
        # Get password from Kubernetes
        try:
            import subprocess
            result = subprocess.run([
                'kubectl', 'get', 'secret', 'kafka-user-passwords', 
                '-n', 'ingestion-ns', '-o', 'jsonpath={.data.client-passwords}'
            ], capture_output=True, text=True, check=True)
            
            import base64
            password = base64.b64decode(result.stdout).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Failed to get Kafka password: {e}")
            password = "your_password_here"  # Fallback
            
        return {
            'bootstrap_servers': ['localhost:9092'],
            'security_protocol': 'SASL_PLAINTEXT',
            'sasl_mechanism': 'PLAIN',
            'sasl_plain_username': 'user1',
            'sasl_plain_password': password,
            'value_serializer': lambda x: json.dumps(x).encode('utf-8'),
            'key_serializer': lambda x: x.encode('utf-8') if x else None,
            'acks': 'all',
            'retries': 3
        }
        
    def create_producer(self):
        """Create Kafka producer"""
        try:
            producer = KafkaProducer(**self.kafka_config)
            logger.info("✅ Kafka producer created successfully")
            return producer
        except Exception as e:
            logger.error(f"❌ Failed to create producer: {e}")
            raise
            
    def send_image_metadata(self, metadata):
        """Send image metadata - topic will be auto-created"""
        try:
            # Prepare message for face.images.metadata topic
            message = {
                'image_id': metadata.get('image_id'),
                'filename': metadata.get('filename'),
                'filepath': metadata.get('filepath'),
                'file_size': metadata.get('file_size'),
                'dimensions': f"{metadata.get('width')}x{metadata.get('height')}",
                'category': metadata.get('category'),
                'face_count': metadata.get('face_count', 0),
                'source_dataset': metadata.get('source_dataset'),
                'dataset_split': metadata.get('dataset_split'),
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'pipeline_version': '1.0'
            }
            
            # Send to face.images.metadata topic (auto-created)
            future = self.producer.send(
                'face.images.metadata',  # Topic auto-created
                key=metadata.get('image_id'),
                value=message
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            logger.info(f"✅ Sent image metadata: {metadata.get('image_id')} → {record_metadata.topic}[{record_metadata.partition}]")
            
            self.stats['images_sent'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send image metadata: {e}")
            return False
            
    def send_face_annotations(self, image_id, annotations):
        """Send face annotations - topic will be auto-created"""
        if not annotations:
            return
            
        try:
            for i, annotation in enumerate(annotations):
                annotation_message = {
                    'annotation_id': f"{image_id}_face_{i}",
                    'image_id': image_id,
                    'face_index': i,
                    'bbox': {
                        'x': annotation.get('bbox_x'),
                        'y': annotation.get('bbox_y'),
                        'width': annotation.get('bbox_width'),
                        'height': annotation.get('bbox_height')
                    },
                    'attributes': {
                        'blur': annotation.get('blur', 0),
                        'expression': annotation.get('expression', 0),
                        'illumination': annotation.get('illumination', 0),
                        'occlusion': annotation.get('occlusion', 0),
                        'pose': annotation.get('pose', 0)
                    },
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
                
                # Send to face.annotations.stream topic (auto-created)
                future = self.producer.send(
                    'face.annotations.stream',  # Topic auto-created
                    key=f"{image_id}_face_{i}",
                    value=annotation_message
                )
                
                future.get(timeout=10)
                self.stats['annotations_sent'] += 1
                
            logger.info(f"✅ Sent {len(annotations)} annotations for {image_id}")
            self.stats['total_faces'] += len(annotations)
            
        except Exception as e:
            logger.error(f"❌ Failed to send annotations for {image_id}: {e}")
            
    def process_metadata_from_file(self, metadata_file):
        """Process metadata file and stream to Kafka"""
        logger.info(f"📂 Processing metadata file: {metadata_file}")
        
        if not os.path.exists(metadata_file):
            logger.error(f"❌ Metadata file not found: {metadata_file}")
            return False
            
        try:
            with open(metadata_file, 'r') as f:
                metadata_list = json.load(f)
                
            logger.info(f"📊 Found {len(metadata_list)} records to process")
            
            for i, metadata in enumerate(metadata_list, 1):
                logger.info(f"🔄 Processing {i}/{len(metadata_list)}: {metadata.get('image_id')}")
                
                # Send image metadata
                if self.send_image_metadata(metadata):
                    # Send face annotations if available
                    annotations = metadata.get('annotations', [])
                    if annotations:
                        self.send_face_annotations(metadata.get('image_id'), annotations)
                
                # Small delay to avoid overwhelming
                time.sleep(0.1)
                
            # Final stats
            logger.info(f"🎉 STREAMING COMPLETE!")
            logger.info(f"   📊 Images sent: {self.stats['images_sent']}")
            logger.info(f"   👥 Annotations sent: {self.stats['annotations_sent']}")
            logger.info(f"   🔢 Total faces: {self.stats['total_faces']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing metadata: {e}")
            return False
            
    def consume_messages(self, topics=['face.images.metadata', 'face.annotations.stream']):
        """Consume messages from topics"""
        try:
            # Consumer configuration
            consumer_config = {
                'bootstrap_servers': ['localhost:9092'],
                'security_protocol': 'SASL_PLAINTEXT',
                'sasl_mechanism': 'PLAIN',
                'sasl_plain_username': 'user1',
                'sasl_plain_password': self.kafka_config['sasl_plain_password'],
                'value_deserializer': lambda x: json.loads(x.decode('utf-8')),
                'key_deserializer': lambda x: x.decode('utf-8') if x else None,
                'group_id': 'face-detection-consumer',
                'auto_offset_reset': 'earliest'
            }
            
            consumer = KafkaConsumer(*topics, **consumer_config)
            logger.info(f"🎧 Started consuming from topics: {topics}")
            
            message_count = 0
            for message in consumer:
                if not self.running:
                    break
                    
                message_count += 1
                self.stats['messages_consumed'] += 1
                
                # Process message based on topic
                if message.topic == 'face.images.metadata':
                    self.process_image_message(message.value)
                elif message.topic == 'face.annotations.stream':
                    self.process_annotation_message(message.value)
                    
                # Stop after processing some messages (for demo)
                if message_count >= 50:  # Process 50 messages then stop
                    logger.info("🛑 Stopping consumer after 50 messages (demo mode)")
                    break
                    
            consumer.close()
            logger.info("📝 Consumer closed")
            
        except Exception as e:
            logger.error(f"❌ Consumer error: {e}")
            
    def process_image_message(self, message):
        """Process image metadata message"""
        image_id = message.get('image_id')
        filename = message.get('filename')
        dimensions = message.get('dimensions')
        face_count = message.get('face_count', 0)
        category = message.get('category')
        
        logger.info(f"🖼️  Processed Image: {filename} ({image_id})")
        logger.info(f"   📏 Size: {dimensions}")
        logger.info(f"   👥 Faces: {face_count}")
        logger.info(f"   📂 Category: {category}")
        
    def process_annotation_message(self, message):
        """Process face annotation message"""
        annotation_id = message.get('annotation_id')
        image_id = message.get('image_id')
        bbox = message.get('bbox', {})
        
        logger.info(f"👤 Processed Annotation: {annotation_id}")
        logger.info(f"   🖼️  Image: {image_id}")
        logger.info(f"   📦 BBox: {bbox.get('x')},{bbox.get('y')},{bbox.get('width')},{bbox.get('height')}")
        
    def run_producer(self, metadata_file):
        """Run producer to send messages"""
        logger.info("🚀 Starting Face Detection Producer...")
        success = self.process_metadata_from_file(metadata_file)
        
        if self.producer:
            self.producer.flush()
            self.producer.close()
            
        return success
        
    def run_consumer(self):
        """Run consumer to receive messages"""
        logger.info("🎧 Starting Face Detection Consumer...")
        self.consume_messages()
        
    def run_streaming_test(self, metadata_file):
        """Run complete streaming test: Producer + Consumer"""
        logger.info("🔄 STARTING FACE DETECTION STREAMING TEST")
        logger.info("=" * 50)
        
        # Start consumer in background thread
        consumer_thread = threading.Thread(target=self.run_consumer)
        consumer_thread.daemon = True
        consumer_thread.start()
        
        # Wait for consumer to initialize
        time.sleep(3)
        
        # Run producer
        producer_success = self.run_producer(metadata_file)
        
        # Let consumer process messages
        time.sleep(5)
        
        # Stop consumer
        self.running = False
        
        # Final results
        logger.info("🎉 STREAMING TEST COMPLETE!")
        logger.info("=" * 30)
        logger.info(f"📊 FINAL STATS:")
        logger.info(f"   Images sent: {self.stats['images_sent']}")
        logger.info(f"   Annotations sent: {self.stats['annotations_sent']}")  
        logger.info(f"   Messages consumed: {self.stats['messages_consumed']}")
        logger.info(f"   Total faces processed: {self.stats['total_faces']}")
        
        return producer_success and self.stats['messages_consumed'] > 0

def main():
    """Main function"""
    metadata_file = "data-pipeline/metadata/sample_metadata.json"
    
    if not os.path.exists(metadata_file):
        logger.error(f"❌ Metadata file not found: {metadata_file}")
        logger.info("💡 Run Step 1 first to generate metadata file")
        return
        
    try:
        # Create streaming pipeline
        streaming = FaceDetectionStreaming()
        
        # Run complete test
        success = streaming.run_streaming_test(metadata_file)
        
        if success:
            logger.info("✅ Face Detection Streaming Pipeline - SUCCESS!")
        else:
            logger.error("❌ Face Detection Streaming Pipeline - FAILED!")
            
    except Exception as e:
        logger.error(f"❌ Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
