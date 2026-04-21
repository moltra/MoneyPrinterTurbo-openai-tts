#!/bin/bash
# Quick test script for small model keyword quality
# Run this tomorrow morning to evaluate gemma:2b vs gemma4:e4b

echo "========================================"
echo "Small Model Quality Test"
echo "========================================"
echo ""

# Download small model if needed
echo "1. Downloading gemma:2b (if not present)..."
docker exec ollama ollama pull gemma:2b

echo ""
echo "2. Testing keyword generation quality..."
echo ""

# Test subject
SUBJECT="home improvement and kitchen renovation"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST SUBJECT: $SUBJECT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test with large model
echo "🔵 LARGE MODEL (gemma4:e4b):"
echo "Generating keywords..."
START=$(date +%s)
docker exec ollama ollama run gemma4:e4b "Generate 5 search keywords for stock videos about: $SUBJECT. Return only a JSON array of strings like [\"keyword1\", \"keyword2\", \"keyword3\", \"keyword4\", \"keyword5\"]"
END=$(date +%s)
LARGE_TIME=$((END-START))
echo ""
echo "⏱️  Time: ${LARGE_TIME}s"
echo ""

# Test with small model
echo "🟢 SMALL MODEL (gemma:2b):"
echo "Generating keywords..."
START=$(date +%s)
docker exec ollama ollama run gemma:2b "Generate 5 search keywords for stock videos about: $SUBJECT. Return only a JSON array of strings like [\"keyword1\", \"keyword2\", \"keyword3\", \"keyword4\", \"keyword5\"]"
END=$(date +%s)
SMALL_TIME=$((END-START))
echo ""
echo "⏱️  Time: ${SMALL_TIME}s"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
SAVINGS=$((LARGE_TIME-SMALL_TIME))
echo "Large model time: ${LARGE_TIME}s"
echo "Small model time: ${SMALL_TIME}s"
echo "Time saved: ${SAVINGS}s"
echo ""
echo "👆 Review the keyword quality above"
echo "   Are the small model keywords good enough?"
echo ""
echo "💾 Model sizes:"
docker exec ollama ollama list | grep -E "gemma4:e4b|gemma:2b"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "DECISION GUIDE:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Use small model if:"
echo "   - Keywords are relevant and useful"
echo "   - Speed difference is significant (>10s)"
echo "   - Quality difference is acceptable"
echo ""
echo "❌ Keep large model if:"
echo "   - Keywords are poor/irrelevant"
echo "   - Quality matters more than speed"
echo ""
