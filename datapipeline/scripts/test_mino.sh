#!/bin/bash

echo "🔍 VERIFYING STEP 1: Minimal Data Pipeline Setup"
echo "=============================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success_count=0
total_checks=6

# Check 1: WIDER_val extraction
echo "1. Dataset Extraction:"
if [ -d "rawdata/WIDER_val" ]; then
    VAL_COUNT=$(find rawdata/WIDER_val -name "*.jpg" 2>/dev/null | wc -l)
    echo -e "   ${GREEN}✅ WIDER_val extracted: $VAL_COUNT images${NC}"
    ((success_count++))
else
    echo -e "   ${RED}❌ WIDER_val not extracted${NC}"
fi

# Check 2: Sample data preparation
echo "2. Sample Data Preparation:"
if [ -d "data-pipeline/sample/images" ]; then
    SAMPLE_COUNT=$(ls data-pipeline/sample/images/*.jpg 2>/dev/null | wc -l)
    if [ $SAMPLE_COUNT -gt 0 ]; then
        echo -e "   ${GREEN}✅ Sample images prepared: $SAMPLE_COUNT files${NC}"
        ((success_count++))
    else
        echo -e "   ${RED}❌ No sample images found${NC}"
    fi
else
    echo -e "   ${RED}❌ Sample images directory not found${NC}"
fi

# Check 3: Metadata generation
echo "3. Metadata Generation:"
if [ -f "data-pipeline/metadata/sample_metadata.json" ]; then
    METADATA_SIZE=$(du -h data-pipeline/metadata/sample_metadata.json | cut -f1)
    METADATA_COUNT=$(jq length data-pipeline/metadata/sample_metadata.json 2>/dev/null || echo "0")
    echo -e "   ${GREEN}✅ Metadata generated: $METADATA_SIZE, $METADATA_COUNT records${NC}"
    ((success_count++))
else
    echo -e "   ${RED}❌ Metadata file not found${NC}"
fi

# Check 4: MinIO connection
echo "4. MinIO Storage Connection:"
if mc admin info local > /dev/null 2>&1; then
    BUCKET_COUNT=$(mc ls local/ | wc -l)
    echo -e "   ${GREEN}✅ MinIO accessible: $BUCKET_COUNT buckets${NC}"
    ((success_count++))
else
    echo -e "   ${RED}❌ MinIO connection failed${NC}"
    echo -e "   ${YELLOW}💡 Hint: Check if port-forward is running: kubectl port-forward --namespace storage-ns svc/minio 9000:9000${NC}"
fi

# Check 5: Data upload verification
echo "5. Data Upload Verification:"
if mc ls local/ > /dev/null 2>&1; then
    IMAGE_COUNT=$(mc ls local/face-images-raw/validation-sample/ 2>/dev/null | wc -l)
    METADATA_COUNT=$(mc ls local/metadata-stream/validation-sample/ 2>/dev/null | wc -l)
    
    if [ $IMAGE_COUNT -gt 0 ] && [ $METADATA_COUNT -gt 0 ]; then
        echo -e "   ${GREEN}✅ Data uploaded successfully${NC}"
        echo -e "      - Images: $IMAGE_COUNT files"
        echo -e "      - Metadata: $METADATA_COUNT files"
        ((success_count++))
    else
        echo -e "   ${RED}❌ Data upload incomplete${NC}"
        echo -e "      - Images: $IMAGE_COUNT files"
        echo -e "      - Metadata: $METADATA_COUNT files"
    fi
else
    echo -e "   ${RED}❌ Cannot verify uploads (MinIO connection issue)${NC}"
fi

# Check 6: Pipeline manifest
echo "6. Pipeline Configuration:"
if [ -f "data-pipeline/pipeline_manifest.json" ]; then
    echo -e "   ${GREEN}✅ Pipeline manifest created${NC}"
    ((success_count++))
else
    echo -e "   ${RED}❌ Pipeline manifest missing${NC}"
fi

# Overall status
echo ""
echo "🎯 STEP 1 COMPLETION STATUS:"
echo "=============================="
if [ $success_count -eq $total_checks ]; then
    echo -e "${GREEN}🟢 SUCCESS: All checks passed ($success_count/$total_checks)${NC}"
    echo -e "${GREEN}🚀 Ready for Step 2: Kafka Topic Creation & Streaming${NC}"
    
    # Show summary
    echo ""
    echo "📊 DATA PIPELINE SUMMARY:"
    echo "========================"
    echo "   Dataset: WIDER_FACE validation (minimal)"
    echo "   Images: $(ls data-pipeline/sample/images/*.jpg 2>/dev/null | wc -l) sample files"
    echo "   Storage: MinIO buckets configured"
    echo "   Metadata: Structured JSON ready for streaming"
    echo "   Status: Foundation layer complete ✅"
    
elif [ $success_count -gt 3 ]; then
    echo -e "${YELLOW}🟡 PARTIAL SUCCESS: ($success_count/$total_checks) - Some issues to resolve${NC}"
    echo -e "${YELLOW}💡 Fix the failed checks above before proceeding${NC}"
else
    echo -e "${RED}🔴 INCOMPLETE: ($success_count/$total_checks) - Major issues need resolution${NC}"
    echo -e "${RED}🛠️  Please fix the errors above before proceeding${NC}"
fi

echo ""
echo "📋 NEXT STEPS:"
echo "=============="
echo "   → Step 2: Create Kafka topics for face detection pipeline"
echo "   → Step 3: Setup Schema Registry with face detection schemas"
echo "   → Step 4: Test end-to-end data streaming"

