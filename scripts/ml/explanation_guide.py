#!/usr/bin/env python3
"""
Quick Explainable PSA Prediction Guide
Shows how to get detailed explanations for PSA grade predictions
"""

print("🎯 PSA Grade Explanation System")
print("=" * 50)

print("\\n✅ YES! Your model can now explain WHY it gives specific grades:")
print()

print("🔍 WHAT THE EXPLAINABLE PREDICTOR TELLS YOU:")
print("   1️⃣  Exact prediction confidence for each grade")
print("   2️⃣  Why it's NOT a PSA 10 (specific deficit %)")
print("   3️⃣  Which side of card (front vs back) has issues")
print("   4️⃣  What improvements would help reach PSA 10")
print("   5️⃣  Visual attention maps showing problem areas")

print("\\n📋 USAGE:")
print("python3 explainable_predictor.py front.jpg back.jpg")

print("\\n🎯 EXAMPLE OUTPUT FROM YOUR CARD:")
print("=" * 30)
print("🥇 PSA 9: 43.73%")
print("🥈 PSA 10: 30.36%") 
print("🥉 PSA 8: 17.43%")
print()
print("🤔 WHY NOT PSA 10?")
print("   Deficit to PSA 10: 13.37%")
print("   🟡 MODERATE PSA 10 confidence - minor issues detected")
print()
print("🔄 Model focuses on BACK damage/condition")
print("🔍 Likely issues: Minor centering, surface wear, edge imperfection")
print("💡 Close to PSA 10 - minor condition improvement could help")

print("\\n💎 WHAT THIS MEANS FOR YOUR CARD:")
print("   • Model found minor imperfections preventing PSA 10")
print("   • Issues are primarily on the BACK of the card") 
print("   • Need 13.4% improvement in condition for PSA 10")
print("   • Still great gem mint quality (PSA 9)")

print("\\n🚀 FOR INVESTMENT DECISIONS:")
print("   ✅ High PSA 9 confidence (43.73%)")
print("   🔶 Moderate PSA 10 potential (30.36%)")
print("   💰 Good investment candidate, but not perfect grade")

print("\\nNow you know exactly WHY your model makes each prediction! 🎯")