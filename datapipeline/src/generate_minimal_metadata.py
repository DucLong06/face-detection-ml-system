import json
import os
import hashlib
from datetime import datetime
from PIL import Image
import sys

def get_file_hash(filepath):
    """Calculate MD5 hash of file"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_image_info(filepath):
    """Get image dimensions and basic info"""
    try:
        with Image.open(filepath) as img:
            return {
                'width': img.size[0],
                'height': img.size[1],
                'mode': img.mode,
                'format': img.format
            }
    except Exception as e:
        print(f"Error reading image {filepath}: {e}")
        return {'width': 0, 'height': 0, 'mode': 'unknown', 'format': 'unknown'}

def parse_wider_annotations(annotation_file):
    """Parse WIDER FACE validation annotations - COMPLETELY REWRITTEN"""
    annotations = {}
    
    if not os.path.exists(annotation_file):
        print(f"⚠️  Annotation file not found: {annotation_file}")
        return annotations
        
    try:
        with open(annotation_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        print(f"📖 Reading annotation file with {len(lines)} lines")
        
        i = 0
        images_parsed = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
                
            # Check if this line contains an image path
            if line.endswith('.jpg') or line.endswith('.jpeg'):
                full_path = line
                image_name = os.path.basename(full_path)
                
                # Move to next line (should be face count)
                i += 1
                if i >= len(lines):
                    print(f"⚠️  Unexpected end of file after image: {image_name}")
                    break
                
                # Parse face count
                face_count_line = lines[i].strip()
                try:
                    face_count = int(face_count_line)
                except ValueError:
                    print(f"⚠️  Invalid face count '{face_count_line}' for {image_name}")
                    i += 1
                    continue
                
                # Parse face annotations
                faces = []
                for j in range(face_count):
                    i += 1
                    if i >= len(lines):
                        print(f"⚠️  Unexpected end of file while reading faces for {image_name}")
                        break
                        
                    face_line = lines[i].strip()
                    if not face_line:
                        print(f"⚠️  Empty face line for {image_name}")
                        continue
                        
                    face_data = face_line.split()
                    if len(face_data) >= 4:
                        try:
                            faces.append({
                                'bbox_x': int(face_data[0]),
                                'bbox_y': int(face_data[1]),
                                'bbox_width': int(face_data[2]),
                                'bbox_height': int(face_data[3]),
                                'blur': int(face_data[4]) if len(face_data) > 4 else 0,
                                'expression': int(face_data[5]) if len(face_data) > 5 else 0,
                                'illumination': int(face_data[6]) if len(face_data) > 6 else 0,
                                'invalid': int(face_data[7]) if len(face_data) > 7 else 0,
                                'occlusion': int(face_data[8]) if len(face_data) > 8 else 0,
                                'pose': int(face_data[9]) if len(face_data) > 9 else 0
                            })
                        except ValueError as e:
                            print(f"⚠️  Error parsing face data '{face_line}' for {image_name}: {e}")
                
                # Store annotation
                annotations[image_name] = {
                    'full_path': full_path,
                    'faces': faces
                }
                
                images_parsed += 1
                if images_parsed <= 5 or images_parsed % 500 == 0:
                    print(f"✅ PARSED: {image_name} -> {len(faces)} faces (total: {images_parsed})")
            
            # Move to next line
            i += 1
            
        print(f"📊 Successfully parsed annotations for {len(annotations)} images")
        
        # Debug: Show some specific annotations we're looking for
        target_files = [
            "24_Soldier_Firing_Soldier_Firing_24_281.jpg",
            "24_Soldier_Firing_Soldier_Firing_24_691.jpg"
        ]
        
        print(f"🎯 Checking for target files:")
        for target in target_files:
            if target in annotations:
                face_count = len(annotations[target]['faces'])
                print(f"  ✅ {target} -> {face_count} faces")
            else:
                print(f"  ❌ {target} -> NOT FOUND")
        
    except Exception as e:
        print(f"❌ Error parsing annotations: {e}")
        import traceback
        traceback.print_exc()
        
    return annotations

def generate_minimal_metadata(images_dir, annotations_file, output_file):
    """Generate metadata for sample images - FIXED VERSION"""
    
    print(f"🔍 Processing images in: {images_dir}")
    
    # Parse annotations
    annotations = parse_wider_annotations(annotations_file)
    
    if not annotations:
        print("❌ No annotations loaded!")
        return []
    
    metadata_list = []
    processed_count = 0
    matched_count = 0
    
    # Get list of image files
    image_files = [f for f in sorted(os.listdir(images_dir)) 
                   if f.lower().endswith(('.jpg', '.jpeg'))]
    
    print(f"📊 Found {len(image_files)} image files to process")
    
    # Process each image in sample directory
    for filename in image_files:
        filepath = os.path.join(images_dir, filename)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        file_hash = get_file_hash(filepath)
        image_info = get_image_info(filepath)
        
        # Extract category from filename (WIDER_val format)
        # Example: 24_Soldier_Firing_Soldier_Firing_24_281.jpg -> category: Soldier_Firing
        parts = filename.split('_')
        if len(parts) >= 2:
            category = parts[1]
        else:
            category = 'unknown'
        
        # Find annotations for this image using exact filename match
        image_annotations = []
        annotation_path = ""
        
        if filename in annotations:
            image_annotations = annotations[filename]['faces']
            annotation_path = annotations[filename]['full_path']
            matched_count += 1
            print(f"✅ MATCHED: {filename} -> {len(image_annotations)} faces")
        else:
            print(f"⚠️  NO MATCH: {filename} (not found in {len(annotations)} annotations)")
        
        # Create metadata record
        metadata = {
            "image_id": os.path.splitext(filename)[0],
            "filename": filename,
            "filepath": f"face-images-raw/validation-sample/{filename}",
            "annotation_path": annotation_path,
            "file_size": file_size,
            "file_hash": file_hash,
            "width": image_info['width'],
            "height": image_info['height'],
            "image_mode": image_info['mode'],
            "format": image_info['format'],
            "category": category,
            "upload_timestamp": datetime.now().isoformat(),
            "source_dataset": "WIDER_FACE",
            "dataset_split": "validation",
            "status": "ready_for_processing",
            "face_count": len(image_annotations),
            "annotations": image_annotations,
            "pipeline_version": "1.0",
            "processing_priority": "normal"
        }
        
        metadata_list.append(metadata)
        processed_count += 1
        
        print(f"✅ Processed: {filename} ({image_info['width']}x{image_info['height']}, {len(image_annotations)} faces)")
    
    # Save metadata
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(metadata_list, f, indent=2)
    
    # Generate summary
    total_faces = sum(item['face_count'] for item in metadata_list)
    avg_faces = total_faces / len(metadata_list) if metadata_list else 0
    
    print(f"\n🎉 METADATA GENERATION COMPLETE:")
    print(f"   📊 Images processed: {len(metadata_list)}")
    print(f"   🔗 Annotations matched: {matched_count}/{len(metadata_list)} ({matched_count/len(metadata_list)*100:.1f}%)")
    print(f"   👥 Total faces: {total_faces}")
    print(f"   📈 Average faces per image: {avg_faces:.1f}")
    print(f"   💾 Saved to: {output_file}")
    
    return metadata_list

if __name__ == "__main__":
    # Configuration
    images_dir = "data-pipeline/sample/images"
    annotations_file = "data-pipeline/sample/annotations/wider_face_val_bbx_gt.txt"
    output_file = "data-pipeline/metadata/sample_metadata.json"
    
    # Check if images directory exists
    if not os.path.exists(images_dir):
        print(f"❌ ERROR: Images directory not found: {images_dir}")
        sys.exit(1)
    
    # Generate metadata
    try:
        metadata = generate_minimal_metadata(images_dir, annotations_file, output_file)
        print(f"\n✅ SUCCESS: Generated metadata for {len(metadata)} images")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)